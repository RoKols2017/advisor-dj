from .services import import_users_from_csv_stream, import_print_events

import logging

logger = logging.getLogger('import')


def import_users_from_csv(file):
    return import_users_from_csv_stream(file)


def import_print_events_from_json(events):
    return import_print_events(events)