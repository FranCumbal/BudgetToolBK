from .schedule_without_categorizer_service import ScheduleWithoutCategorizerService
from .schedule_with_categorizer_service import ScheduleWithCategorizerService
from .manual_planning_service import ManualPlanningService

class PlanningServiceFactory:
    """Factory para crear servicios de planificación según el tipo"""
    
    SERVICE_TYPES = {
        "schedule_without_categorizer": ScheduleWithoutCategorizerService,
        "schedule_with_categorizer": ScheduleWithCategorizerService,
        "default": ManualPlanningService  # Para backward compatibility
    }
    
    @classmethod
    def create_service(cls, service_type: str, line_title: str = None):
        """
        Crea un servicio de planificación según el tipo especificado
        
        Args:
            service_type: Tipo de servicio ('schedule_without_categorizer', 'schedule_with_categorizer', 'default')
            line_title: Título de la línea de campo
            
        Returns:
            Instancia del servicio apropiado
        """
        service_class = cls.SERVICE_TYPES.get(service_type, ManualPlanningService)
        return service_class(line_title)
    
    @classmethod
    def get_service_type_from_line_reports(cls, line_title: str, field_line_reports: list) -> str:
        """
        Determina el tipo de servicio basado en la lista de instancias de reportes
        Args:
            line_title: Título de la línea
            field_line_reports: Lista de instancias de FieldReport (o hijas)
        Returns:
            Tipo de servicio correspondiente
        """
        for report in field_line_reports:
            if hasattr(report, "title") and report.title == line_title:
                return getattr(report, "type", "default")
        return "default"
