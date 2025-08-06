from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

def upgrade():
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)

    # --- Room Table ---
    if 'room' in inspector.get_table_names():
        room_columns = [col['name'] for col in inspector.get_columns('room')]
        with op.batch_alter_table('room', schema=None) as batch_op:
            # Drop legacy 'is_available' column if present
            if 'is_available' in room_columns:
                batch_op.drop_column('is_available')
            # Add missing 'dirty_until' column
            if 'dirty_until' not in room_columns:
                batch_op.add_column(sa.Column('dirty_until', sa.DateTime(), nullable=True))
            # Add 'maintenance_notes' if missing
            if 'maintenance_notes' not in room_columns:
                batch_op.add_column(sa.Column('maintenance_notes', sa.Text(), nullable=True))
        # Ensure no NULL status values
        conn.execute("UPDATE room SET status = 'available' WHERE status IS NULL")

    # --- Guest Table ---
    if 'guest' in inspector.get_table_names():
        guest_columns = [col['name'] for col in inspector.get_columns('guest')]
        guest_indexes = [idx['name'] for idx in inspector.get_indexes('guest')]
        with op.batch_alter_table('guest', schema=None) as batch_op:
            # Make email nullable
            batch_op.alter_column('email', existing_type=sa.String(120), nullable=True)
            # Add unique constraint to 'phone'
            if 'guest_phone_key' not in guest_indexes:
                batch_op.create_unique_constraint('guest_phone_key', ['phone'])

    # --- Booking Table ---
    if 'booking' in inspector.get_table_names():
        booking_columns = [col['name'] for col in inspector.get_columns('booking')]
        with op.batch_alter_table('booking', schema=None) as batch_op:
            for col_name, col_type in [
                ('cancelled_at', sa.DateTime()),
                ('auto_cancel_time', sa.DateTime())
            ]:
                if col_name not in booking_columns:
                    batch_op.add_column(sa.Column(col_name, col_type, nullable=True))

    # --- Staff Table ---
    if 'staff' in inspector.get_table_names():
        staff_columns = [col['name'] for col in inspector.get_columns('staff')]
        with op.batch_alter_table('staff', schema=None) as batch_op:
            if 'role' not in staff_columns:
                batch_op.add_column(sa.Column('role', sa.String(20), nullable=False))
            if 'full_name' not in staff_columns:
                batch_op.add_column(sa.Column('full_name', sa.String(100), nullable=False))
            if 'is_active' not in staff_columns:
                batch_op.add_column(sa.Column('is_active', sa.Boolean(), default=True))

def downgrade():
    with op.batch_alter_table('room', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_available', sa.Boolean(), default=True))

    with op.batch_alter_table('guest', schema=None) as batch_op:
        batch_op.alter_column('email', existing_type=sa.String(120), nullable=False)
        batch_op.drop_constraint('guest_phone_key', type_='unique')

    with op.batch_alter_table('booking', schema=None) as batch_op:
        batch_op.drop_column('cancelled_at')
        batch_op.drop_column('auto_cancel_time')

    with op.batch_alter_table('staff', schema=None) as batch_op:
        batch_op.drop_column('role')
        batch_op.drop_column('full_name')
        batch_op.drop_column('is_active')
