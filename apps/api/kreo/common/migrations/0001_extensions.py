from django.contrib.postgres.operations import TrigramExtension, UnaccentExtension
from django.db import migrations


class Migration(migrations.Migration):
    """Extensions PostgreSQL et configuration de recherche french + unaccent."""

    initial = True
    dependencies = []

    operations = [
        migrations.RunSQL(
            "CREATE EXTENSION IF NOT EXISTS pgcrypto;",
            reverse_sql="DROP EXTENSION IF EXISTS pgcrypto;",
        ),
        TrigramExtension(),
        UnaccentExtension(),
        migrations.RunSQL(
            sql="""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_ts_config WHERE cfgname = 'kreo_french'
                ) THEN
                    CREATE TEXT SEARCH CONFIGURATION kreo_french (COPY = french);
                    ALTER TEXT SEARCH CONFIGURATION kreo_french
                        ALTER MAPPING FOR hword, hword_part, word, asciiword, asciihword, hword_asciipart
                        WITH unaccent, french_stem;
                END IF;
            END
            $$;
            """,
            reverse_sql="DROP TEXT SEARCH CONFIGURATION IF EXISTS kreo_french;",
        ),
    ]
