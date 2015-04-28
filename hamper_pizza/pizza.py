from collections import defaultdict
import datetime
import re
import time

from hamper.interfaces import ChatCommandPlugin, Command
from hamper.utils import ude

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base

from twisted.internet import reactor

SQLAlchemyBase = declarative_base()


class Pizza(ChatCommandPlugin):
    """ Vote on which pizzas to buy. """

    name = 'pizza'

    priority = 1

    short_desc = 'Vote on which pizza you want to eat.'
    long_desc = ('!pizza <duration> - Start a pizza poll with a given duration'
                 ' in minutes.\n'
                 '!vote <option>')

    poll_id = 0

    def setup(self, loader):
        super(Pizza, self).setup(loader)
        self.db = loader.db
        SQLAlchemyBase.metadata.create_all(self.db.engine)

    def poll_exists(self):
        poll = self.db.session.query(PizzaPoll).filter(
                    PizzaPoll.endtime > datetime.datetime.now()
                ).first()

        if poll:
            print poll.id
            print poll.endtime
            print datetime.datetime.now()
            return True

    def close_poll(self, bot, comm):
        """
        Closes the current Pizza poll.
        """

        # Get all the votes. This could probably be done better without 
        # defaultdict, but I'm in a time crunch :p
        db_votes = self.db.session.query(PizzaVote).filter(
            PizzaVote.poll_id == self.poll_id
            ).all()

        votes = defaultdict(int)
        for vote in db_votes:
            votes[vote.option] += 1

        # Sorts by the number of votes on a given option
        # Reverse so we go highest to lowest.
        options = list(reversed(sorted(votes.items(), key=lambda x: x[1])))
        num_options = 5 if len(options) > 5 else len(options)

        option_and_vote = '{:^20} | {:^8}'

        # Generate the reply string
        bot.reply(comm, 'The pizza poll is over! And the results are:')
        bot.reply(comm, '{:^20}   {:^8}'.format('Option', 'Votes'))
        bot.reply(comm, '_______________________________')
        for x in xrange(num_options):
            bot.reply(comm, option_and_vote.format(
                        options[x][0], options[x][1]))

        print "Done printing stuff"

    class StartPoll(Command):
        name = 'pizza'
        regex = r'^pizza (\d+)?$'

        short_desc = ('!pizza <duration> - Start a pizza poll with a given '
                      'duration in minutes. (Default duration is 10 minutes)')

        def command(self, bot, comm, groups):
            print "intercepted pizza command"
            if self.plugin.poll_exists():
                return bot.reply(comm, '{0}, there is already a pizza poll '
                        'right now!'.format(comm['user']))

            # reactor.callLater takes it's arguments as floats.
            duration = float(groups[0])

            db = self.plugin.db
            poll_id = self.plugin.poll_id
            args = (bot, comm)
            reactor.callLater(duration * 60, self.plugin.close_poll, *args)

            poll = PizzaPoll(duration)
            db.session.add(poll)
            db.session.commit()

            self.plugin.poll_id = poll.id

            bot.reply(comm, "{0} has initiated a pizza poll!".format(
                        comm['user']))

    class Vote(Command):
        name = 'vote'
        regex = r'^vote \"(.+)\"$'

        short_desc = '!vote - Which pizza option to vote for.'

        def command(self, bot, comm, groups):
            if not self.plugin.poll_exists():
                return bot.reply(comm, '{0}, there is no pizza poll right '
                        'now!'.format(comm['user']))

            if not self.plugin.db.session.query(PizzaVote).filter(
                    PizzaVote.user == comm['user'],
                    PizzaVote.poll_id == self.plugin.poll_id
                ).first():

                print groups
                vote = PizzaVote(comm['user'], groups[0], self.plugin.poll_id)

                self.plugin.db.session.add(vote)
                self.plugin.db.session.commit()

                bot.reply(comm, '{0}, your vote for \'{1}\' has been '
                            'cast!'.format(comm['user'], groups[0]))
            else:
                bot.reply(comm, '{0}, you have already voted!'.format(
                            comm['user']))


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

    __tablename__ = 'pizza_votes'

    id = Column(Integer, primary_key=True)
    user = Column(String)
    option = Column(String)
    poll_id = Column(Integer) # I'll add a FK to this later.

    def __init__(self, user, option, poll_id):
        self.user = user
        self.option = option
        self.poll_id = poll_id

pizza = Pizza()
