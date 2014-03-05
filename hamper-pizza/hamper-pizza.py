from collections import defaultdict
import datetime
import re
import time

from hamper.interfaces import ChatCommandPlugin, Command
from hamper.utils import ude

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base

from twisted.internet import defer

SQLAlchemyBase = declarative_base()


class Pizza(ChatCommandPlugin):
    """ Vote on which pizzas to buy. """

    name = 'pizza'

    priority = 1

    short_desc = 'Vote on which pizza you want to eat.'
    long_desc = ('!pizza <duration> - Start a pizza poll with a given duration'
                 ' in minutes.\n'
                 '!vote <option>')

    def setup(self, loader):
        super(Pizza, self).setup(loader)
        self.db = loader.db
        SQLAlchemyBase.metadata.create_all(self.db.engine)

    def poll_exists(self):
        if not self.plugin.db.session.query(PizzaPoll).filter(
                PizzaPoll.endtime < datetime.datetime.now()).first():
                    return False
        return True

    def start_poll(self, duration, bot, comm):
        # We assume duration is sent in as seconds.
        # time.sleep() uses milliseconds
        time.sleep(1000 * duration)

        # Get all the votes. This could probably be done better without 
        # defaultdict but I'm in a time crunch :p
        votes = defaultdict(int)
        db_votes = self.db.session.query(PizzaVote).all()
        for vote in db_votes:
            votes[vote] += 1

        # Sorts by the number of votes on a given option, and reverses
        # the list since by default it goes from lowest to highest
        options = reversed(sorted(votes.items(), lambda x: x[1]))

        num_options = 5 if len(sorted_votes) > 5 else len(sorted_votes)
        option_and_vote = '{:^20} | {:^8}'

        # Generate the reply string
        reply = ('The pizza poll is over! And the results are:'
                '{:^20} {:^8}\n____________________________'.format(
                    'Option', 'Votes'))
        reply += '\n'.join([option_and_vote.format(options[0], options[1])
                             for x in xrange(num_options)])

        bot.reply(comm, reply)


    class Pizza(Command):
        name = 'pizza'
        regex = r'^pizza (\d)$'

        short_desc = ('!pizza <duration> - Start a pizza poll with a given '
                      'duration in minutes. (Default duration is 10 minutes)')

        def command(self, bot, comm, groups):
            if self.plugin.poll_exists():
                return ('{0}, there is already a pizza poll right '
                        'now!'.format(comm['user']))

            d = defer.Deferred()
            d.callback(groups[0], bot, comm)
            d.addCallback(start_poll)


    class Vote(Command):
        name = 'vote'
        regex = r'^vote [[\"(.+)\"$]|[(.+)]]'

        short_desc = '!vote - Which pizza option to vote for.'

        def command(self, bot, comm, groups):
            if not self.plugin.poll_exists():
                return bot.reply(comm, '{0}, there is no pizza poll right '
                        'now!'.format(comm['user']))

            if not self.plugin.db.session.query(PizzaVote).filter(
                PizzaVote.user == comm['user']).first():
                vote = PizzaVote(comm['user'], groups[0])

                self.plugin.db.session.add(vote)
                self.plugin.db.session.commit()

                bot.reply(comm, '{0}, your vote for \'{1}\' has been '
                            ' cast!'.format(comm['user'], groups[0]))
            else:
                bot.reply(comm, '{0}, you have already voted!')


class PizzaPoll(SQLAlchemyBase):
    """
    Stsrt a pizza poll for a certain duration.
    """

    __tablename__ = 'pizza_poll'

    id = Column(Integer, primary_key=True)
    endtime = Column(DateTime)

    def __init__(self, duration=10):
        self.endtime = self.calculate_end(duration)

    def calculate_end(self, duration):
        return datetime.datetime.now() + datetime.timedelta(minutes=duration)


class PizzaVote(SQLAlchemyBase):
    """
    A vote for a single player on which pizza to get.
    """

    id = Column(Integer, primary_key=True)
    user = Column(String)
    option = Column(String)

    def __init__(self, user, option):
        self.user = user
        self.option = option

pizza = Pizza()
