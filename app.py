import os
import sys
import datetime
from flask import Flask
from flask import request
from flask_restful import (
    abort,
    reqparse,
    inputs,
    fields,
    marshal_with,
    Api,
    Resource
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import asc, desc

app = Flask(__name__)
api = Api(app)
db = SQLAlchemy(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///event.db'


events_fields = {
    'id': fields.Integer,
    'event': fields.String,
    'date': fields.String
}

data_fields = {
    'data': events_fields
}


class Event(db.Model):
    """Event ORM class"""
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    event = db.Column(db.String(80), nullable=False)
    date = db.Column(db.Date, nullable=False)

    def __repr__(self):
        return f"{self.id} - {self.event} - {self.date}"


if not os.path.exists('event.db'):
    db.create_all()


# write your code here

def get_events(query_set):
    context = []
    for el in query_set:
        event_date = el.date.strftime("%Y-%m-%d")
        event_model = EventModel(id=el.id, event=el.event, date=event_date)
        context.append(event_model)
    return context


class EventModel:
    """Represent model for json"""

    def __init__(self, id, event, date):
        self.id = id
        self.event = event
        self.date = date


@api.resource('/event/today')
class HelloWorldResource(Resource):
    """Retrieve all event posts if they match with today time"""

    @marshal_with(events_fields)
    def get(self):
        query_set = Event.query.filter(Event.date == datetime.date.today()).all()
        return get_events(query_set)


@api.resource('/event')
class PostEvent(Resource):
    """Post event in db"""

    parser = reqparse.RequestParser()
    parser.add_argument(
        'date',
        type=inputs.date,
        help="The event date with the correct format is required!"
             " The correct format is YYYY-MM-DD!",
        required=True
    )
    parser.add_argument(
        'event',
        type=str,
        help="The event name is required!",
        required=True
    )

    @marshal_with(events_fields)
    def get(self):
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')

        if start_time is not None and end_time is not None:
            query_set = Event.query.filter(start_time <= Event.date).filter(Event.date <= end_time) \
                .order_by(desc(Event.id))
            if query_set.count() == 1:
                event_model = query_set.first()
                print(event_model)
                return EventModel(id=event_model.id, event=event_model.event, date=event_model.date)
        else:
            query_set = Event.query.all()
        return get_events(query_set)

    def post(self):
        args = self.parser.parse_args()
        args['date'] = str(args['date'].date())
        date = datetime.datetime.strptime(args['date'], "%Y-%m-%d")

        event = Event(event=args['event'], date=date)

        db.session.add(event)
        db.session.commit()
        args["message"] = "The event has been added!"
        return args


@api.resource('/event/<int:event_id>')
class RetrieveEvent(Resource):
    """Retrieve event post from db"""

    parser = reqparse.RequestParser()

    @marshal_with(events_fields)
    def get(self, event_id):
        event = Event.query.filter(Event.id == event_id).first()
        if event is not None:
            return EventModel(id=event.id, event=event.event, date=event.date)
        else:
            abort(404, message="The event doesn't exist!")

    def delete(self, event_id):
        args = self.parser.parse_args()
        event = Event.query.filter(Event.id == event_id).first()
        if event is not None:
            db.session.delete(event)
            db.session.commit()
            args['message'] = "The event has been deleted!"
        else:
            abort(404, message="The event doesn't exist!")
        return args


# do not change the way you run the program
if __name__ == '__main__':
    if len(sys.argv) > 1:
        arg_host, arg_port = sys.argv[1].split(':')
        app.run(host=arg_host, port=arg_port)
    else:
        app.run()
