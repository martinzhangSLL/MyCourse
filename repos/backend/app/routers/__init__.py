from app.routers.auth import router as auth_router
from app.routers.class_router import router as class_router
from app.routers.config_router import router as config_router
from app.routers.term_router import router as term_router
from app.routers.teacher_router import router as teacher_router
from app.routers.course_router import router as course_router, class_course_router
from app.routers.settlement_router import router as settlement_router
from app.routers.student_router import router as student_router
from app.routers.score_router import router as score_router, teacher_score_router
from app.routers.ranking_router import router as ranking_router

__all__ = ["auth_router", "class_router", "config_router", "term_router", "teacher_router", "course_router", "class_course_router", "settlement_router", "student_router", "score_router", "teacher_score_router", "ranking_router"]
