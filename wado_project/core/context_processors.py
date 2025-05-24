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
            {'name': 'Профиль коменданта', 'url_name': 'commandant:profile', 'active': False},
            {'name': 'Наряды', 'url_name': 'commandant:duty:list', 'active': False},
        ]
    elif user_type == 'faculty':
        menu_items = [
            {'name': 'Профиль факультета', 'url_name': 'faculty:profile', 'active': False},
            {'name': 'Личный состав', 'url_name': 'faculty:staff', 'active': False},
        ]
    elif user_type == 'department':
        menu_items = [
            {'name': 'Профиль кафедры', 'url_name': 'department:profile', 'active': False},
            {'name': 'Личный состав', 'url_name': 'department:people:staff', 'active': False},
            {'name': 'Освобождения', 'url_name': 'department:missing:department_list', 'active': False},
            {'name': 'Допуски', 'url_name': 'department:permission:department_list', 'active': False},
        ]

    for item in menu_items:
        try:
            item['url'] = reverse(item['url_name'])
            item['active'] = current_path.startswith(item['url'])
        except:
            item['url'] = '#'
            item['active'] = False

    return {
        'user_type': user_type,
        'menu_items': menu_items
    }