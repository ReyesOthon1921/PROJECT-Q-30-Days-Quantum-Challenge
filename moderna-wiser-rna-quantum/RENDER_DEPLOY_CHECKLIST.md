# RNAQ Render Integration Checklist

This patch integrates the guided 3-minute demo into the main Flask app.

Routes added:
- `/mvp-demo`
- `/rnaq-demo`

It does not replace the existing dashboard. It keeps Render using `wsgi:app`.

Expected Render settings:
- Root Directory: `moderna-wiser-rna-quantum`
- Build Command: `pip install -r requirements-deploy.txt`
- Start Command: `gunicorn wsgi:app --bind 0.0.0.0:$PORT`
- Branch: `main`

After applying:
1. Run `python -m py_compile app.py rnaq_labs_demo_app.py`.
2. Run `python -m pytest tests\test_rnaq_labs_demo_packet.py -q`.
3. Run `python -m pytest tests -q`.
4. Commit and push to `main`.
5. Check the live route: `/mvp-demo`.
