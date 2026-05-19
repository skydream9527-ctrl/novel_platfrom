from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.deps import get_current_user
from ..models.models import WritingGoal, WritingLog, Chapter, Task

router = APIRouter(prefix="/writing", tags=["writing"])


class WritingGoalCreate(BaseModel):
    task_id: int
    goal_type: str  # daily / weekly / total
    target_words: int
    start_date: datetime | None = None
    end_date: datetime | None = None


class WritingGoalUpdate(BaseModel):
    target_words: int | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None


class WritingLogCreate(BaseModel):
    task_id: int
    chapter_id: int | None = None
    words_written: int
    duration_seconds: int | None = None


@router.get("/goals/by-task/{task_id}")
async def get_writing_goals(task_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """获取写作目标"""
    result = await db.execute(
        select(WritingGoal).where(WritingGoal.task_id == task_id)
    )
    goals = result.scalars().all()

    return [
        {
            "id": g.id,
            "task_id": g.task_id,
            "goal_type": g.goal_type,
            "target_words": g.target_words,
            "start_date": g.start_date.isoformat() if g.start_date else None,
            "end_date": g.end_date.isoformat() if g.end_date else None,
            "created_at": g.created_at.isoformat(),
        }
        for g in goals
    ]


@router.post("/goals")
async def create_writing_goal(req: WritingGoalCreate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """创建写作目标"""
    goal = WritingGoal(
        task_id=req.task_id,
        goal_type=req.goal_type,
        target_words=req.target_words,
        start_date=req.start_date,
        end_date=req.end_date,
    )
    db.add(goal)
    await db.commit()
    await db.refresh(goal)

    return {
        "id": goal.id,
        "goal_type": goal.goal_type,
        "target_words": goal.target_words,
    }


@router.patch("/goals/{goal_id}")
async def update_writing_goal(goal_id: int, req: WritingGoalUpdate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """更新写作目标"""
    result = await db.execute(select(WritingGoal).where(WritingGoal.id == goal_id))
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=404, detail="Writing goal not found")

    if req.target_words is not None:
        goal.target_words = req.target_words
    if req.start_date is not None:
        goal.start_date = req.start_date
    if req.end_date is not None:
        goal.end_date = req.end_date

    await db.commit()

    return {"ok": True}


@router.delete("/goals/{goal_id}")
async def delete_writing_goal(goal_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """删除写作目标"""
    result = await db.execute(select(WritingGoal).where(WritingGoal.id == goal_id))
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=404, detail="Writing goal not found")

    await db.delete(goal)
    await db.commit()

    return {"ok": True}


@router.post("/logs")
async def create_writing_log(req: WritingLogCreate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """创建写作记录"""
    log = WritingLog(
        task_id=req.task_id,
        chapter_id=req.chapter_id,
        words_written=req.words_written,
        duration_seconds=req.duration_seconds,
    )
    db.add(log)
    await db.commit()

    return {"ok": True}


@router.get("/stats/by-task/{task_id}")
async def get_writing_stats(task_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """获取写作统计数据"""
    # 今日字数
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    result = await db.execute(
        select(func.sum(WritingLog.words_written)).where(
            and_(
                WritingLog.task_id == task_id,
                WritingLog.recorded_at >= today_start
            )
        )
    )
    today_words = result.scalar() or 0

    # 本周字数
    week_start = today_start - timedelta(days=today.weekday())
    result = await db.execute(
        select(func.sum(WritingLog.words_written)).where(
            and_(
                WritingLog.task_id == task_id,
                WritingLog.recorded_at >= week_start
            )
        )
    )
    week_words = result.scalar() or 0

    # 总字数（从章节内容计算）
    result = await db.execute(
        select(func.sum(func.length(Chapter.content))).where(Chapter.task_id == task_id)
    )
    total_words = result.scalar() or 0

    # 写作天数统计
    result = await db.execute(
        select(func.count(func.distinct(func.date(WritingLog.recorded_at)))).where(
            WritingLog.task_id == task_id
        )
    )
    writing_days = result.scalar() or 0

    # 平均速度（字/小时）
    result = await db.execute(
        select(
            func.sum(WritingLog.words_written),
            func.sum(WritingLog.duration_seconds)
        ).where(WritingLog.task_id == task_id)
    )
    row = result.one()
    total_written = row[0] or 0
    total_seconds = row[1] or 0
    avg_speed = (total_written / (total_seconds / 3600)) if total_seconds > 0 else 0

    return {
        "today_words": today_words,
        "week_words": week_words,
        "total_words": total_words,
        "writing_days": writing_days,
        "avg_speed": round(avg_speed),
    }


@router.get("/stats/by-task/{task_id}/daily")
async def get_daily_stats(
    task_id: int,
    days: int = Query(30, description="统计天数"),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取每日字数统计"""
    start_date = datetime.now() - timedelta(days=days)

    result = await db.execute(
        select(
            func.date(WritingLog.recorded_at).label("date"),
            func.sum(WritingLog.words_written).label("words")
        ).where(
            and_(
                WritingLog.task_id == task_id,
                WritingLog.recorded_at >= start_date
            )
        ).group_by(func.date(WritingLog.recorded_at))
        .order_by(func.date(WritingLog.recorded_at))
    )

    daily_stats = [
        {"date": str(row.date), "words": row.words}
        for row in result.all()
    ]

    return daily_stats


@router.get("/stats/streak")
async def get_writing_streak(task_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """获取连续写作天数"""
    # 获取所有写作日期
    result = await db.execute(
        select(
            func.distinct(func.date(WritingLog.recorded_at)).label("date")
        ).where(WritingLog.task_id == task_id)
        .order_by(func.date(WritingLog.recorded_at).desc())
    )
    dates = [row.date for row in result.all()]

    if not dates:
        return {"streak": 0}

    # 计算连续天数
    streak = 0
    today = datetime.now().date()

    for i, date in enumerate(dates):
        expected_date = today - timedelta(days=i)
        if date == expected_date:
            streak += 1
        else:
            break

    return {"streak": streak}
