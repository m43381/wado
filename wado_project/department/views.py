# department/views.py

from django.views.generic import TemplateView
from django.db.models import Count, Avg
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from people.models import People
from core.mixins import HasDepartmentMixin


class DepartmentDashboardView(HasDepartmentMixin, TemplateView):
    template_name = 'profiles/department/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        staff_stats = People.objects.filter(department=user.department).aggregate(
            total=Count('id'),
            avg_workload=Avg('workload')
        )

        # Формируем данные для информационной таблицы
        profile_info_items = [
            {"label": "Имя пользователя", "value": user.username},
            {"label": "Факультет", "value": user.faculty or "-"},
            {"label": "Статус", "value": "Активный"},
        ]
        info_grid = render_to_string('components/info-grid.html', {'items': profile_info_items}, request=self.request)

        # Формируем данные для статистики
        stats = [
            {"icon": "users", "value": staff_stats['total'], "label": "Сотрудников"},
            {"icon": "tasks", "value": f"{round(staff_stats['avg_workload'], 1) if staff_stats['avg_workload'] else 0}", "label": "Средняя нагрузка"},
        ]
        stat_cards = render_to_string('components/stat-cards.html', {'stats': stats}, request=self.request)

        context.update({
            'user': user,
            'staff_count': staff_stats['total'],
            'avg_workload': round(staff_stats['avg_workload'], 1) if staff_stats['avg_workload'] else 0.0,
            'recent_staff': People.objects.filter(department=user.department).order_by('-id')[:5],
            'department': user.department,
            'faculty': user.faculty,

            # HTML-фрагменты
            'info_grid': mark_safe(info_grid),
            'stat_cards': mark_safe(stat_cards),
        })

        return context