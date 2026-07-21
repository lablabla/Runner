"""SQLAlchemy models. Importing this package registers all tables on ``Base``."""
from app.models.activity import Activity
from app.models.credential import IntegrationCredential
from app.models.daily_metric import DailyMetric
from app.models.insight import Insight
from app.models.planned_workout import PlannedWorkout
from app.models.user import User
from app.models.weather import Weather

__all__ = [
    "Activity",
    "IntegrationCredential",
    "DailyMetric",
    "Insight",
    "PlannedWorkout",
    "User",
    "Weather",
]
