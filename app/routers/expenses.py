import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.category import Category
from app.models.expense import Expense
from app.models.expense_split import ExpenseSplit
from app.models.group import Group
from app.models.group_member import GroupMember
from app.models.user import User
from app.schemas.expenses import (
    ExpenseCreate,
    ExpenseResponse,
    ExpenseSplitResponse,
    ExpenseUpdate,
)
from app.services.split_calculator import SplitCalculator

router = APIRouter(prefix="/api/expenses", tags=["expenses"])


async def _get_group_member_ids(group_id: uuid.UUID, db: AsyncSession) -> list[str]:
    """Get all active member user IDs for a group as strings."""
    result = await db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.is_active == True,
        )
    )
    members = result.scalars().all()
    return [str(m.user_id) for m in members]


async def _expense_to_response(expense: Expense, db: AsyncSession) -> ExpenseResponse:
    """Build an ExpenseResponse with splits populated."""
    splits_result = await db.execute(
        select(ExpenseSplit).where(ExpenseSplit.expense_id == expense.id)
    )
    splits = splits_result.scalars().all()

    split_responses = [
        ExpenseSplitResponse(
            id=s.id,
            user_id=s.user_id,
            amount=s.amount,
            percentage=s.percentage,
            shares=s.shares,
        )
        for s in splits
    ]

    return ExpenseResponse(
        id=expense.id,
        group_id=expense.group_id,
        paid_by=expense.paid_by,
        category_id=expense.category_id,
        amount=expense.amount,
        description=expense.description,
        currency=expense.currency,
        split_type=expense.split_type,
        expense_date=expense.expense_date,
        is_active=expense.is_active,
        created_at=expense.created_at,
        updated_at=expense.updated_at,
        splits=split_responses,
    )


@router.get("/group/{group_id}", response_model=list[ExpenseResponse])
async def list_group_expenses(
    group_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Expense).where(
            Expense.group_id == group_id,
            Expense.is_active == True,
        )
    )
    expenses = result.scalars().all()

    responses = []
    for expense in expenses:
        responses.append(await _expense_to_response(expense, db))
    return responses


@router.get("/{expense_id}", response_model=ExpenseResponse)
async def get_expense(
    expense_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Expense).where(Expense.id == expense_id))
    expense = result.scalar_one_or_none()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return await _expense_to_response(expense, db)


@router.post("/", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
async def create_expense(
    data: ExpenseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Validate group exists
    group_result = await db.execute(select(Group).where(Group.id == data.group_id))
    group = group_result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Validate category exists
    cat_result = await db.execute(select(Category).where(Category.id == data.category_id))
    if not cat_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Category not found")

    # Get group member IDs
    member_ids = await _get_group_member_ids(data.group_id, db)
    if not member_ids:
        raise HTTPException(status_code=400, detail="Group has no members")

    # Calculate splits
    try:
        split_amounts = SplitCalculator.calculate(
            total_amount=data.amount,
            split_type=data.split_type,
            splits=data.splits,
            participant_ids=member_ids,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Create expense
    expense = Expense(
        group_id=data.group_id,
        paid_by=current_user.id,
        category_id=data.category_id,
        amount=data.amount,
        description=data.description,
        currency=data.currency,
        split_type=data.split_type,
        expense_date=data.expense_date,
    )
    db.add(expense)
    await db.flush()
    await db.refresh(expense)

    # Create expense splits
    for split_data in split_amounts:
        split = ExpenseSplit(
            expense_id=expense.id,
            user_id=uuid.UUID(split_data["user_id"]),
            amount=split_data["amount"],
        )
        db.add(split)

    await db.flush()
    return await _expense_to_response(expense, db)


@router.put("/{expense_id}", response_model=ExpenseResponse)
async def update_expense(
    expense_id: uuid.UUID,
    data: ExpenseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Expense).where(Expense.id == expense_id))
    expense = result.scalar_one_or_none()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    if data.category_id is not None:
        cat_result = await db.execute(select(Category).where(Category.id == data.category_id))
        if not cat_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Category not found")
        expense.category_id = data.category_id
    if data.amount is not None:
        expense.amount = data.amount
    if data.description is not None:
        expense.description = data.description
    if data.currency is not None:
        expense.currency = data.currency
    if data.split_type is not None:
        expense.split_type = data.split_type
    if data.expense_date is not None:
        expense.expense_date = data.expense_date
    if data.is_active is not None:
        expense.is_active = data.is_active

    await db.flush()
    await db.refresh(expense)
    return await _expense_to_response(expense, db)


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(
    expense_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Expense).where(Expense.id == expense_id))
    expense = result.scalar_one_or_none()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    await db.delete(expense)
    await db.flush()
    return JSONResponse(status_code=200, content="Expense deleted successfully!")