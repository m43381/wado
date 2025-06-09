from django.urls import reverse
from .utils import get_user_type

def sidebar_menu(request):
    if not request.user.is_authenticated:
        return {'menu_items': []}

    menu_items = []
    current_path = request.path
    user_type = get_user_type(request.user)

    if user_type == 'commandant':
        menu_items = [
            {'name': 'Профиль коменданта', 'url_name': 'commandant:profile'},
            {'name': 'Наряды', 'url_name': 'commandant:duty:list'},
            {'name': 'Личный состав', 'url_name': 'commandant:staff'},
            {'name': 'Уведомления', 'url_name': 'notifications:list'},
        ]
    elif user_type == 'faculty':
        menu_items = [
            {'name': 'Профиль факультета', 'url_name': 'faculty:profile'},
            {'name': 'Л/с факультета', 'url_name': 'faculty:staff'},
            {'name': 'Л/с управления факультета', 'url_name': 'faculty:people:staff'},
            {'name': 'Допуски к нарядам', 'url_name': 'faculty:permission:faculty_list'},
            {'name': 'Освобождения', 'url_name': 'faculty:missing:faculty_list'},
            {'name': 'Наряды', 'url_name': 'faculty:duty:list'},
            {'name': 'Уведомления', 'url_name': 'notifications:list'},
        ]
    elif user_type == 'department':
        menu_items = [
            {'name': 'Профиль кафедры', 'url_name': 'department:profile'},
            {'name': 'Личный состав', 'url_name': 'department:people:staff'},
            {'name': 'Освобождения', 'url_name': 'department:missing:department_list'},
            {'name': 'Допуски', 'url_name': 'department:permission:department_list'},
            {'name': 'Наряды', 'url_name': 'department:duty:list'},
            {'name': 'Уведомления', 'url_name': 'notifications:list'},
        ]

    # Добавляем URL и проверку активности
    for item in menu_items:
        try:
            item['url'] = reverse(item['url_name'])
            item['active'] = item['url'].rstrip('/') == current_path.rstrip('/')
        except Exception as e:
            item['url'] = '#'
            item['active'] = False

    unread_count = request.user.received_notifications.filter(is_read=False).count()

    return {
        'user_type': user_type,
        'menu_items': menu_items,
        'unread_notifications': unread_count
    }