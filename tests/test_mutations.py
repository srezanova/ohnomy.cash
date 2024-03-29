from collections import OrderedDict
from django.test import RequestFactory, TestCase
from unittest import skip
from django.core.exceptions import ValidationError
from graphene.test import Client

from users.models import CustomUser
from budget.models import Transaction as TransactionModel
from budget.models import Category as CategoryModel
from budget.models import Month as MonthModel
from budget.models import Plan as PlanModel
from checkBalance.schema import schema


TestCase.maxDiff = None


def execute_query(query, user=None, variable_values=None, **kwargs):
    """
    Returns the results of executing a graphQL query using the graphene test client.
    """
    task_factory = RequestFactory()
    context_value = task_factory.get('/graphql/')
    context_value.user = user
    client = Client(schema)
    executed = client.execute(
        query, context_value=context_value, variable_values=variable_values, **kwargs)
    return executed


class QueryTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create(
            id=100,
            email='user@test.com',
            password='testpassword',
        )

        self.user1 = CustomUser.objects.create_user(
            email='user1@test.com',
            password='testpassword',
            username='test_user1'
        )

        self.month = MonthModel.objects.create(
            id=200,
            user=self.user,
            month=1,
            year=2021,
            start_month_savings=100,
            start_month_balance=100,
        )

        self.month1 = MonthModel.objects.create(
            id=201,
            user=self.user1,
            month=1,
            year=2021,
            start_month_savings=100,
            start_month_balance=100,
        )

        self.category = CategoryModel.objects.create(
            id=300,
            user=self.user,
            name='Dogs',
        )

        self.category1 = CategoryModel.objects.create(
            id=301,
            user=self.user,
            name='Food',
        )

        self.transaction = TransactionModel.objects.create(
            id=400,
            user=self.user,
            category=self.category,
            month=self.month,
            amount=1000,
            description='test',
            group='Expense'
        )

        self.transaction1 = TransactionModel.objects.create(
            id=401,
            user=self.user1,
            month=self.month1,
            amount=1000,
            description='test second user',
            group='Expense'
        )

        self.plan = PlanModel.objects.create(
            id=500,
            user=self.user,
            category=self.category,
            month=self.month,
            planned_amount=10,
        )

    def tearDown(self):
        self.user.delete()
        self.user1.delete()
        self.month.delete()
        self.month1.delete()
        self.category.delete()
        self.category1.delete()
        self.transaction.delete()
        self.transaction1.delete()
        self.plan.delete()

    def test_register_mutation(self):
        query = '''
            mutation {
                register (email:"test@test.com",
                    password:"testpassword",
                    username:"test_register") {
                        email
                }
            }
                '''

        expected = {
            'register': {
                'email': 'test@test.com'
            }
        }

        executed = execute_query(query, self.user)
        data = executed.get('data')
        self.assertEqual(data, expected)

    def test_login_mutation(self):
        query = '''
            mutation {
                login (password:"testpassword", email:"user1@test.com") {
                    token
                }
            }
                '''

        executed = execute_query(query, self.user1)
        keys = str(executed.keys())
        expected = "dict_keys(['data'])"
        self.assertEqual(keys, expected)

    def test_create_transaction_mutation(self):
        query = '''
            mutation {
                createTransaction(amount:100,
                group:Expense,
                month:200) {
                    amount
                    group
                    month {
                        id
                    }
                }
            }
                '''

        expected = OrderedDict([
            ('createTransaction', {'amount': 100,
                                   'group': 'EXPENSE',
                                   'month': {'id': '200'}})])

        executed = execute_query(query, self.user)
        data = executed.get('data')
        self.assertEqual(data, expected)

    def test_create_transaction_mutation_user1(self):
        query = '''
            mutation {
                createTransaction(amount:100,
                    group:Expense,
                    month:201,
                    category:300) {
                        amount
                        group
                        category {
                            id
                        }
                        month {
                            id
                        }
                }
            }
                '''

        expected = OrderedDict([('createTransaction', {
            'amount': 100, 'group': 'EXPENSE',
            'category': None,
            'month': {'id': '201'}})])

        executed = execute_query(query, self.user1)
        data = executed.get('data')
        self.assertEqual(data, expected)

    def test_create_transactions_mutation_user(self):
        query = '''
            mutation {
                createTransactions(transactions:
                [{amount:100, month:201, group:Expense},
                {amount:200, month:200, category:300, group:Savings},
                {amount:300, month:200, category:305, group:Income},
                {amount:400, month:200, group:Expense},
                ]) {
                    transactions {
                        amount
                        category {
                            id
                        }
                    }
                }
            }
                '''

        expected = OrderedDict([('createTransactions', {'transactions': [
            {'amount': 200, 'category': {'id': '300'}},
            {'amount': 300, 'category': None},
            {'amount': 400, 'category': None}]})])

        executed = execute_query(query, self.user)
        data = executed.get('data')
        self.assertEqual(data, expected)

    def test_update_transaction_mutation(self):
        query = '''
                mutation {
                updateTransaction (
                    id:400,
                    amount:888,
                    category:301 ) {
                        id
                        amount
                        category {
                            id
                        }
                    }
                }
                '''

        expected = OrderedDict([('updateTransaction',
                                 {'id': '400', 'amount': 888,
                                  'category': {'id': '301'}})])

        executed = execute_query(query, self.user)
        data = executed.get('data')
        self.assertEqual(data, expected)

    def test_update_transaction_mutation_user1(self):
        query = '''
                mutation {
                updateTransaction (
                    id:401,
                    amount:888,
                    category:301 ) {
                        id
                        amount
                        category {
                            id
                        }
                    }
                }
                '''

        expected = OrderedDict([('updateTransaction',
                                 {'id': '401', 'amount': 888,
                                  'category': None})])

        executed = execute_query(query, self.user1)
        data = executed.get('data')
        self.assertEqual(data, expected)

    def test_delete_transaction_mutation(self):
        query = '''
            mutation {
                deleteTransaction(id:401) {
                    id
                }
            }
                '''

        expected = {"deleteTransaction": None}

        executed = execute_query(query, self.user1)
        data = executed.get('data')
        self.assertEqual(data, expected)

    def test_create_category_mutation(self):
        query = '''
            mutation {
                createCategory(name:"Stocks", color:"red") {
                    name
                    color
                }
            }
                '''

        expected = OrderedDict(
            [('createCategory', {'name': 'Stocks', 'color': 'red'})])

        executed = execute_query(query, self.user)
        data = executed.get('data')
        self.assertEqual(data, expected)

    def test_update_category_mutation(self):
        query = '''
            mutation {
                updateCategory(id:300, name:"Deposit", color:"yellow") {
                    name
                    color
                }
            }
                '''

        expected = OrderedDict(
            [('updateCategory', {'name': 'Deposit', 'color': 'yellow'})])

        executed = execute_query(query, self.user)
        data = executed.get('data')
        self.assertEqual(data, expected)

    def test_delete_category_mutation(self):
        query = '''
            mutation {
                deleteCategory(id:300) {
                    id
                }
            }
                '''

        expected = {"deleteCategory": None}

        executed = execute_query(query, self.user)
        data = executed.get('data')
        self.assertEqual(data, expected)

    def test_create_month_mutation(self):
        query = '''
            mutation {
                createMonth(month:0,
                year:2021) {
                    month
                    year
                    startMonthSavings
                    startMonthBalance
                }
            }
                '''

        expected = OrderedDict([('createMonth', {
                               'month': 0,
                               'year': 2021,
                               'startMonthSavings': 0,
                               'startMonthBalance': 0})])

        executed = execute_query(query, self.user)
        data = executed.get('data')
        self.assertEqual(data, expected)

    @skip('works')
    def test_create_month_mutation_validation(self):
        query = '''
            mutation {
                createMonth(month:12,
                year:2021) {
                    month
                    year
                    startMonthSavings
                    startMonthBalance
                }
            }
                '''

        expected = OrderedDict([('createMonth', {
                               'month': 12,
                               'year': 2021,
                               'startMonthSavings': 0,
                               'startMonthBalance': 0})])

        executed = execute_query(query, self.user)
        errors = executed.get('errors')[0]['message']
        expected = "['12 not in range (0,11)']"
        self.assertEqual(errors, expected)

    def test_update_month_mutation(self):
        query = '''
            mutation {
                updateMonth(id:200,
                startMonthSavings:1000) {
                    month
                    year
                    startMonthSavings
                    startMonthBalance
                }
            }
                '''

        expected = OrderedDict([('updateMonth', {
                               'month': 1,
                               'year': 2021,
                               'startMonthSavings': 1000,
                               'startMonthBalance': 100})])

        executed = execute_query(query, self.user)
        data = executed.get('data')
        self.assertEqual(data, expected)

    def test_create_plan_mutation(self):
        query = '''
            mutation {
                createPlan(month:200,
                category:300,
                plannedAmount:1000) {
                    plannedAmount
                }
            }
                '''

        expected = OrderedDict([('createPlan', {'plannedAmount': 1000})])

        executed = execute_query(query, self.user)
        data = executed.get('data')
        self.assertEqual(data, expected)

    def test_update_plan_mutation(self):
        query = '''
            mutation {
                updatePlan(id:500,
                plannedAmount:777) {
                    id
                    plannedAmount
                }
            }
                '''

        expected = OrderedDict(
            [('updatePlan', {'id': '500', 'plannedAmount': 777})])

        executed = execute_query(query, self.user)
        data = executed.get('data')
        self.assertEqual(data, expected)
