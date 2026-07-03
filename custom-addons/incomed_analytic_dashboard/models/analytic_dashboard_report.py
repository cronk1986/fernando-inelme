import logging

from odoo import fields, models, tools

_logger = logging.getLogger(__name__)


class AnalyticDashboardReport(models.Model):
    """SQL-based report for analytic dashboard with debit/credit/balance."""

    _name = "analytic.dashboard.report"
    _description = "Informe Tablero Analítico"
    _auto = False
    _rec_name = "analytic_account_id"
    _order = "parent_analytic_id, analytic_account_id"

    analytic_account_id = fields.Many2one(
        comodel_name="account.analytic.account",
        string="Cuenta analítica",
        readonly=True,
    )
    parent_analytic_id = fields.Many2one(
        comodel_name="account.analytic.account",
        string="Cuenta analítica madre",
        readonly=True,
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Cliente",
        readonly=True,
    )
    plan_id = fields.Many2one(
        comodel_name="account.analytic.plan",
        string="Plan",
        readonly=True,
    )
    ref = fields.Char(
        string="Referencia",
        readonly=True,
    )
    date = fields.Date(
        string="Fecha",
        readonly=True,
    )
    debit = fields.Monetary(
        string="Debe",
        readonly=True,
        currency_field="currency_id",
    )
    credit = fields.Monetary(
        string="Haber",
        readonly=True,
        currency_field="currency_id",
    )
    balance = fields.Monetary(
        string="Saldo",
        readonly=True,
        currency_field="currency_id",
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Moneda",
        readonly=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Compañía",
        readonly=True,
    )
    move_type = fields.Char(
        string="Tipo de movimiento",
        readonly=True,
    )

    def init(self):
        """Create SQL view. Uses parent_id from account_analytic_parent (OCA)."""
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    aal.id AS id,
                    aal.account_id AS analytic_account_id,
                    COALESCE(aaa.parent_id, aaa.id) AS parent_analytic_id,
                    aal.partner_id AS partner_id,
                    aaa.plan_id AS plan_id,
                    aal.ref AS ref,
                    aal.date AS date,
                    CASE WHEN aal.amount < 0 THEN ABS(aal.amount) ELSE 0.0 END AS debit,
                    CASE WHEN aal.amount >= 0 THEN aal.amount ELSE 0.0 END AS credit,
                    aal.amount AS balance,
                    aal.currency_id AS currency_id,
                    aal.company_id AS company_id,
                    am.move_type AS move_type
                FROM account_analytic_line aal
                JOIN account_analytic_account aaa ON aaa.id = aal.account_id
                LEFT JOIN account_move_line aml ON aml.id = aal.move_line_id
                LEFT JOIN account_move am ON am.id = aml.move_id
                WHERE aal.account_id IS NOT NULL
            )
        """ % self._table)

    def action_open_analytic_entries(self):
        """Open detailed analytic lines (Margen bruto drill-down)."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Margen bruto - Detalle",
            "res_model": "account.analytic.line",
            "view_mode": "list,pivot,graph",
            "domain": [("account_id", "=", self.analytic_account_id.id)],
            "context": {"default_account_id": self.analytic_account_id.id},
        }
