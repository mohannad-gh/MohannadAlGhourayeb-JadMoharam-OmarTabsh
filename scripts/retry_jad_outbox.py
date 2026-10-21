"""Retry durable audit/notification deliveries after dependencies recover."""
from common.jad_support import flush_outbox
from services.incidents.app import create_app as incidents
from services.notifications.app import create_app as notifications
from services.playbooks.app import create_app as playbooks


if __name__ == '__main__':
    for factory in (notifications, incidents, playbooks):
        app = factory()
        with app.app_context():
            warnings = flush_outbox()
            print(app.config['SERVICE_NAME'], warnings or 'Pending batch delivered (up to 100 events)')
