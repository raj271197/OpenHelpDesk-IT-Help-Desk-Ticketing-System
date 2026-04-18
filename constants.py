TICKET_CATEGORIES = ('Software', 'Hardware', 'Network', 'Other')
TICKET_PRIORITIES = ('Low', 'Medium', 'High')
TICKET_STATUSES = ('Open', 'In Progress', 'Resolved')

PRIORITY_STYLES = {
    'Low': 'secondary',
    'Medium': 'warning',
    'High': 'danger',
}

STATUS_STYLES = {
    'Open': 'danger',
    'In Progress': 'warning',
    'Resolved': 'success',
}

MIN_PASSWORD_LENGTH = 8
MAX_NAME_LENGTH = 120
MAX_EMAIL_LENGTH = 120
MAX_TITLE_LENGTH = 255
MAX_DESCRIPTION_LENGTH = 4000
MAX_COMMENT_LENGTH = 2000
