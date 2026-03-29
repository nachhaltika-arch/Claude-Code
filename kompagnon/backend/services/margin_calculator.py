"""
Real-time margin calculator for KOMPAGNON projects.
Margin target: 78% (minimum 70%)
"""
from sqlalchemy.orm import Session
from database import Project, TimeTracking
from typing import Dict, Optional


class MarginCalculator:
    """Calculate project profitability in real-time."""

    FIXED_PRICE = 2000.0  # €
    DEFAULT_HOURLY_RATE = 45.0  # €
    DEFAULT_AI_COSTS = 50.0  # €
    TARGET_MARGIN_PERCENT = 78
    MIN_ACCEPTABLE_MARGIN_PERCENT = 70
    TARGET_HOURS = 8.5  # hours (total project target)

    @staticmethod
    def calculate_margin(db: Session, project_id: int) -> Dict:
        """
        Calculate current margin for a project.

        Returns:
            {
                'human_hours': float,
                'human_costs': float,
                'ai_tool_costs': float,
                'total_costs': float,
                'margin_eur': float,
                'margin_percent': float,
                'hours_remaining_at_target': float,
                'status': 'green'|'yellow'|'red',
                'alert': bool,
                'target_margin': 78,
                'min_acceptable_margin': 70
            }
        """
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {"error": "Project not found"}

        # Get all time tracking entries
        time_entries = db.query(TimeTracking).filter(
            TimeTracking.project_id == project_id
        ).all()

        # Calculate human hours (exclude KI-logged time from total hours)
        human_hours = sum(
            entry.hours for entry in time_entries
            if entry.logged_by != "KI"
        )

        hourly_rate = project.hourly_rate or MarginCalculator.DEFAULT_HOURLY_RATE
        ai_costs = project.ai_tool_costs or MarginCalculator.DEFAULT_AI_COSTS

        # Cost calculations
        human_costs = human_hours * hourly_rate
        total_costs = human_costs + ai_costs
        fixed_price = project.fixed_price or MarginCalculator.FIXED_PRICE

        # Margin calculations
        if fixed_price > 0:
            margin_eur = fixed_price - total_costs
            margin_percent = (margin_eur / fixed_price) * 100
        else:
            margin_eur = 0
            margin_percent = 0

        # Hours remaining to reach 70% target margin
        target_margin_eur = fixed_price * (MarginCalculator.MIN_ACCEPTABLE_MARGIN_PERCENT / 100)
        remaining_budget_eur = target_margin_eur - ai_costs
        hours_remaining_at_min = remaining_budget_eur / hourly_rate if hourly_rate > 0 else 0
        hours_remaining_at_min = max(0, hours_remaining_at_min)

        # Status determination
        if margin_percent >= MarginCalculator.TARGET_MARGIN_PERCENT:
            status = "green"
            alert = False
        elif margin_percent >= MarginCalculator.MIN_ACCEPTABLE_MARGIN_PERCENT:
            status = "yellow"
            alert = False
        else:
            status = "red"
            alert = True

        # Additional alert if:
        # - Hours exceed target by > 1 hour (8.5h target)
        # - Margin drops below minimum
        if human_hours > MarginCalculator.TARGET_HOURS + 1:
            alert = True

        return {
            "human_hours": round(human_hours, 2),
            "human_costs": round(human_costs, 2),
            "ai_tool_costs": round(ai_costs, 2),
            "total_costs": round(total_costs, 2),
            "margin_eur": round(margin_eur, 2),
            "margin_percent": round(margin_percent, 1),
            "hours_remaining_at_target": round(hours_remaining_at_min, 1),
            "status": status,
            "alert": alert,
            "target_margin": MarginCalculator.TARGET_MARGIN_PERCENT,
            "min_acceptable_margin": MarginCalculator.MIN_ACCEPTABLE_MARGIN_PERCENT,
        }

    @staticmethod
    def update_project_margin(db: Session, project_id: int) -> Optional[float]:
        """
        Calculate and update project's margin_percent field.
        Returns updated margin_percent or None if failed.
        """
        margin_data = MarginCalculator.calculate_margin(db, project_id)
        if "error" in margin_data:
            return None

        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.margin_percent = margin_data["margin_percent"]
            project.actual_hours = margin_data["human_hours"]
            db.commit()
            return project.margin_percent
        return None

    @staticmethod
    def get_all_margins(db: Session) -> Dict[int, Dict]:
        """Get margin data for all active projects."""
        projects = db.query(Project).filter(
            Project.status.in_(["phase_1", "phase_2", "phase_3", "phase_4", "phase_5", "phase_6", "phase_7"])
        ).all()

        margins = {}
        for project in projects:
            margins[project.id] = MarginCalculator.calculate_margin(db, project.id)

        return margins

    @staticmethod
    def get_margin_summary(db: Session) -> Dict:
        """Get overall margin statistics for dashboard."""
        margins_data = MarginCalculator.get_all_margins(db)

        if not margins_data:
            return {
                "active_projects": 0,
                "average_margin_percent": 0,
                "projects_in_target": 0,
                "projects_at_risk": 0,
            }

        valid_margins = [m for m in margins_data.values() if "error" not in m]

        if not valid_margins:
            return {
                "active_projects": 0,
                "average_margin_percent": 0,
                "projects_in_target": 0,
                "projects_at_risk": 0,
            }

        average_margin = sum(m["margin_percent"] for m in valid_margins) / len(valid_margins)
        projects_in_target = sum(1 for m in valid_margins if m["status"] == "green")
        projects_at_risk = sum(1 for m in valid_margins if m["status"] == "red")

        return {
            "active_projects": len(valid_margins),
            "average_margin_percent": round(average_margin, 1),
            "projects_in_target": projects_in_target,
            "projects_at_risk": projects_at_risk,
        }

    @staticmethod
    def log_time(
        db: Session,
        project_id: int,
        hours: float,
        logged_by: str,
        phase: Optional[int] = None,
        activity_description: Optional[str] = None,
    ) -> TimeTracking:
        """Log hours and automatically update margin."""
        time_entry = TimeTracking(
            project_id=project_id,
            phase=phase,
            logged_by=logged_by,
            hours=hours,
            activity_description=activity_description,
        )
        db.add(time_entry)
        db.commit()

        # Auto-update project margin
        MarginCalculator.update_project_margin(db, project_id)

        return time_entry
