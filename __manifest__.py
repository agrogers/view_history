{
    'name': 'View History Logger',
    'summary': 'Log model and record id when opening form views',
    'author': 'Hoang Minh Hieu',
    'version': '18.0.1.0.0',
    'license': 'LGPL-3',
    'depends': ['web', 'base'],
    'data': [
        'security/ir.model.access.csv',
        'security/view_history_rules.xml',
        'views/res_users_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'view_history/static/src/view_history_systray.css',
            'view_history/static/src/form_view_logger.js',
            'view_history/static/src/view_history_systray.xml',
            'view_history/static/src/view_history_systray.js',
        ],
    },
    'images': ['static/description/main_screenshot.png'],
}
