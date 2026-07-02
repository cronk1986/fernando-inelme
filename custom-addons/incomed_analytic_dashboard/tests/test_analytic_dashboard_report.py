from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestAnalyticDashboardReport(TransactionCase):
    """Tests for analytic.dashboard.report SQL view model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.plan = cls.env["account.analytic.plan"].create({
            "name": "Plan Test Dashboard",
        })
        cls.parent_account = cls.env["account.analytic.account"].create({
            "name": "Obra Principal Test",
            "plan_id": cls.plan.id,
        })
        cls.child_account = cls.env["account.analytic.account"].create({
            "name": "Obra Hija Test",
            "plan_id": cls.plan.id,
            "parent_id": cls.parent_account.id,
        })
        cls.partner = cls.env["res.partner"].create({
            "name": "Cliente Test Dashboard",
        })
        cls.analytic_line_expense = cls.env["account.analytic.line"].create({
            "name": "Gasto test",
            "account_id": cls.child_account.id,
            "partner_id": cls.partner.id,
            "amount": -500.0,
            "date": "2026-01-15",
        })
        cls.analytic_line_income = cls.env["account.analytic.line"].create({
            "name": "Ingreso test",
            "account_id": cls.child_account.id,
            "partner_id": cls.partner.id,
            "amount": 1200.0,
            "date": "2026-01-20",
        })

    def test_sql_view_exists(self):
        """SQL view is created and returns records."""
        records = self.env["analytic.dashboard.report"].search([
            ("analytic_account_id", "=", self.child_account.id),
        ])
        self.assertEqual(len(records), 2)

    def test_debit_credit_split(self):
        """Debit/credit are split correctly from amount."""
        expense = self.env["analytic.dashboard.report"].search([
            ("analytic_account_id", "=", self.child_account.id),
            ("debit", ">", 0),
        ])
        self.assertTrue(expense)
        self.assertAlmostEqual(expense[0].debit, 500.0, places=2)
        self.assertAlmostEqual(expense[0].credit, 0.0, places=2)

        income = self.env["analytic.dashboard.report"].search([
            ("analytic_account_id", "=", self.child_account.id),
            ("credit", ">", 0),
        ])
        self.assertTrue(income)
        self.assertAlmostEqual(income[0].credit, 1200.0, places=2)

    def test_parent_analytic_resolved(self):
        """parent_analytic_id resolves to parent via account_analytic_parent."""
        reports = self.env["analytic.dashboard.report"].search([
            ("analytic_account_id", "=", self.child_account.id),
        ])
        for report in reports:
            self.assertEqual(report.parent_analytic_id.id, self.parent_account.id)

    def test_action_open_entries(self):
        """Drill-down action returns correct window action."""
        report = self.env["analytic.dashboard.report"].search([
            ("analytic_account_id", "=", self.child_account.id),
        ], limit=1)
        action = report.action_open_analytic_entries()
        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "account.analytic.line")
        self.assertIn(
            ("account_id", "=", self.child_account.id),
            action["domain"],
        )

    def test_dashboard_record_created(self):
        """Spreadsheet dashboard record exists after install."""
        dashboard = self.env["spreadsheet.dashboard"].search([
            ("name", "=", "Analítica"),
        ])
        self.assertTrue(dashboard)
        self.assertTrue(dashboard.spreadsheet_binary_data)
