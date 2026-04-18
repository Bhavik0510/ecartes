# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0.html)

"""Customer invoice actions ship with kanban; a bad merged kanban arch can crash the
web client (kanban_arch_parser reads field.type before validating the field exists).
Strip kanban from invoice-style window actions so list/form remain usable."""

_INVOICE_STYLE_ACTION_XMLIDS = (
    "account.action_move_out_invoice",
    "account.action_move_out_invoice_type",
    "account.action_move_out_refund_type",
    "account.action_move_in_invoice",
    "account.action_move_in_invoice_type",
    "account.action_move_in_refund_type",
    "account.action_move_out_receipt_type",
    "account.action_move_in_receipt_type",
)


def strip_kanban_from_invoice_window_actions(env):
    for xid in _INVOICE_STYLE_ACTION_XMLIDS:
        act = env.ref(xid, raise_if_not_found=False)
        if not act or act._name != "ir.actions.act_window":
            continue
        vm = act.view_mode or ""
        if "kanban" not in vm:
            continue
        modes = [m.strip() for m in vm.split(",") if m.strip() and m.strip() != "kanban"]
        if modes:
            act.write({"view_mode": ",".join(modes)})


def post_init_hook(env):
    strip_kanban_from_invoice_window_actions(env)
