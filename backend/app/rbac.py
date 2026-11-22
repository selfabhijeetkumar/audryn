"""
AUDRYN Role-Based Access Control (RBAC) Architecture.
Defines roles, permissions, and server-side policy enforcement.
"""
from enum import Enum
from typing import Set, Dict, List


class Role(str, Enum):
    ASSOCIATE = "Associate"
    SENIOR = "Senior"
    MANAGER = "Manager"
    PARTNER = "Partner"


class Permission(str, Enum):
    # Evidence permissions
    READ_EVIDENCE = "READ_EVIDENCE"
    UPLOAD_EVIDENCE = "UPLOAD_EVIDENCE"
    VERIFY_EVIDENCE = "VERIFY_EVIDENCE"
    ACCEPT_EVIDENCE = "ACCEPT_EVIDENCE"

    # Investigation & Agents
    EXECUTE_INVESTIGATION = "EXECUTE_INVESTIGATION"
    VIEW_INVESTIGATION = "VIEW_INVESTIGATION"

    # Counter-Evidence
    VIEW_COUNTER_EVIDENCE = "VIEW_COUNTER_EVIDENCE"
    CREATE_CHALLENGE = "CREATE_CHALLENGE"

    # Findings & Reviews
    CREATE_FINDING = "CREATE_FINDING"
    REQUEST_ADDITIONAL_EVIDENCE = "REQUEST_ADDITIONAL_EVIDENCE"
    ESCALATE_FINDING = "ESCALATE_FINDING"
    APPROVE_FINDING = "APPROVE_FINDING"  # Reserved exclusively for Partner (Brass sign-off)
    REJECT_FINDING = "REJECT_FINDING"

    # Completeness & Not-Checked
    VIEW_COMPLETENESS = "VIEW_COMPLETENESS"
    UPDATE_NOT_CHECKED = "UPDATE_NOT_CHECKED"

    # Calculations & Tax
    RUN_CALCULATIONS = "RUN_CALCULATIONS"
    RUN_TAX_RULES = "RUN_TAX_RULES"

    # Reports
    GENERATE_DRAFT_REPORT = "GENERATE_DRAFT_REPORT"
    FINALIZE_REPORT = "FINALIZE_REPORT"

    # Engagement & Administration
    MANAGE_TEAM = "MANAGE_TEAM"
    CONFIGURE_SETTINGS = "CONFIGURE_SETTINGS"
    VIEW_AUDIT_LOG = "VIEW_AUDIT_LOG"


# Hierarchical Role-Permission Mapping
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.ASSOCIATE: {
        Permission.READ_EVIDENCE,
        Permission.UPLOAD_EVIDENCE,
        Permission.VIEW_INVESTIGATION,
        Permission.VIEW_COUNTER_EVIDENCE,
        Permission.VIEW_COMPLETENESS,
        Permission.VIEW_AUDIT_LOG,
    },
    Role.SENIOR: {
        Permission.READ_EVIDENCE,
        Permission.UPLOAD_EVIDENCE,
        Permission.VERIFY_EVIDENCE,
        Permission.EXECUTE_INVESTIGATION,
        Permission.VIEW_INVESTIGATION,
        Permission.VIEW_COUNTER_EVIDENCE,
        Permission.CREATE_CHALLENGE,
        Permission.REQUEST_ADDITIONAL_EVIDENCE,
        Permission.VIEW_COMPLETENESS,
        Permission.UPDATE_NOT_CHECKED,
        Permission.RUN_CALCULATIONS,
        Permission.RUN_TAX_RULES,
        Permission.VIEW_AUDIT_LOG,
    },
    Role.MANAGER: {
        Permission.READ_EVIDENCE,
        Permission.UPLOAD_EVIDENCE,
        Permission.VERIFY_EVIDENCE,
        Permission.ACCEPT_EVIDENCE,
        Permission.EXECUTE_INVESTIGATION,
        Permission.VIEW_INVESTIGATION,
        Permission.VIEW_COUNTER_EVIDENCE,
        Permission.CREATE_CHALLENGE,
        Permission.CREATE_FINDING,
        Permission.REQUEST_ADDITIONAL_EVIDENCE,
        Permission.ESCALATE_FINDING,
        Permission.VIEW_COMPLETENESS,
        Permission.UPDATE_NOT_CHECKED,
        Permission.RUN_CALCULATIONS,
        Permission.RUN_TAX_RULES,
        Permission.GENERATE_DRAFT_REPORT,
        Permission.CONFIGURE_SETTINGS,
        Permission.VIEW_AUDIT_LOG,
    },
    Role.PARTNER: {
        # Partner has comprehensive statutory sign-off authority
        Permission.READ_EVIDENCE,
        Permission.UPLOAD_EVIDENCE,
        Permission.VERIFY_EVIDENCE,
        Permission.ACCEPT_EVIDENCE,
        Permission.EXECUTE_INVESTIGATION,
        Permission.VIEW_INVESTIGATION,
        Permission.VIEW_COUNTER_EVIDENCE,
        Permission.CREATE_CHALLENGE,
        Permission.CREATE_FINDING,
        Permission.REQUEST_ADDITIONAL_EVIDENCE,
        Permission.ESCALATE_FINDING,
        Permission.APPROVE_FINDING,  # Brass human sign-off
        Permission.REJECT_FINDING,
        Permission.VIEW_COMPLETENESS,
        Permission.UPDATE_NOT_CHECKED,
        Permission.RUN_CALCULATIONS,
        Permission.RUN_TAX_RULES,
        Permission.GENERATE_DRAFT_REPORT,
        Permission.FINALIZE_REPORT,
        Permission.MANAGE_TEAM,
        Permission.CONFIGURE_SETTINGS,
        Permission.VIEW_AUDIT_LOG,
    },
}


def has_permission(role_str: str, permission: Permission) -> bool:
    """Evaluates whether a role possesses a specified permission."""
    try:
        role = Role(role_str)
        return permission in ROLE_PERMISSIONS.get(role, set())
    except ValueError:
        return False
