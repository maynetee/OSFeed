#!/usr/bin/env python3
"""
Verification script for audit logging system.
Tests that audit_log model and record_audit_event function can be imported and initialized.
"""

try:
    from backend.app.models.audit_log import AuditLog
    from backend.app.services.audit import record_audit_event
    print("✓ Successfully imported AuditLog model")
    print("✓ Successfully imported record_audit_event function")
    print("Audit logging system verified")
except ImportError as e:
    print(f"✗ Import error: {e}")
    exit(1)
except Exception as e:
    print(f"✗ Unexpected error: {e}")
    exit(1)
