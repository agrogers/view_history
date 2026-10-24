{
    'name': 'View History Logger',
    'summary': 'Keep a personal history of recently viewed records',
    'description': """
View History Logger keeps a personal list of records you have recently opened in Odoo.
Open the history icon in the backend systray to find an item and return to it without
searching for it again.

Features
--------
* Automatically records opened form views and list views. List history is only recorded
  when you have read access to the model.
* Shows up to 100 recent entries in a backend systray dropdown, with record names and
  available model or record icons.
* Opens a record directly from its history entry; list-view entries return to the
  corresponding model's list.
* Keeps history separate for each user and lets each user enable or disable logging
  in their preferences. Logging is enabled by default.
* Skips temporary (transient) models and omits records that are no longer available
  or that you can no longer read.

To use the feature, open forms or lists as usual, then select the history icon in the
backend systray. Use the View History option in your user preferences to stop recording
new entries. This setting does not affect other users.
""",
    'author': 'Hoang Minh Hieu',
    'version': '18.0.1.0.0',
    'license': 'LGPL-3',
    'depends': ['web', 'base'],
    'data': [
        'security/ir.model.access.csv',
        'security/view_history_rules.xml',
        'views/res_users_view.xml',
        'views/ir_model_views.xml',
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
