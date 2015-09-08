"""Interface to Prolog interpreter."""
import pyswip

from pygdl.languages.prolog import PrologTerm


class QueryEvaluatesFalseError(Exception):
    def __init__(self, query):
        self.query = query

    def __str__(self):
        return "Query: " + self.query


class PrologSession(object):
    """Interface to a SWI-Prolog session

    Wrapper around pyswip.Prolog with added useful methods.
    """
    def __init__(self):
        self._prolog = pyswip.Prolog()

    def query(self, query_term):
        """Execute query_term and return results.

        Returns an iterable of assignments, where each assignment is
        a dictionary that maps Variable => PrologTerm.

        If the query has no variables and is satisfied, a single '[]'
        PrologTerm is yielded.

        WARNING: The returned iterator must be consumed or closed before
        executing the next query.
        """
        for assignment in self._prolog.query(str(query_term), normalize=False):
            if isinstance(assignment, pyswip.Atom):
                yield PrologTerm.make_from_pyswip_term(assignment)
            else:
                yield {str(equality.args[0]):
                       PrologTerm.make_from_pyswip_term(equality.args[1])
                       for equality in assignment}

    def consult(self, filename):
        """Read filename as a Prolog source file."""
        self._prolog.consult(filename)

    def query_first(self, query_term):
        """Evaluate query_term and return the first assignment.

        Raises QueryEvaluatesFalseError if the query has no satisyfing
        assignment.
        """
        query_results = self.query(query_term)
        try:
            result = next(query_results)
            query_results.close()
            return result
        except StopIteration as e:
            raise QueryEvaluatesFalseError(str(query_term)) from e

    def require_query(self, query_term):
        """Execute query_term and raise exception if it evaluates false.

        Exception raised is QueryEvaluatesFalseError
        """
        if not self.query_satisfied(query_term):
            raise QueryEvaluatesFalseError(query_term)

    def query_satisfied(self, query_term):
        """Return True if query_term has at least 1 satisfying assignment."""
        query_results = self.query(query_term)
        try:
            next(query_results)
            query_results.close()
            return True
        except StopIteration:
            return False
