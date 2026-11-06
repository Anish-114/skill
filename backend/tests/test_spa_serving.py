from pathlib import Path
from fastapi.responses import FileResponse
from app.main import app, serve_spa_root, serve_spa_catch_all, health_check, root
from app.db.session import SessionLocal

def test_spa_serving():
    static_dir = Path(__file__).parent.parent / "app" / "static"
    print("Static dir exists:", static_dir.exists())
    assert (static_dir / "index.html").exists()

    # 1. Test root handler
    root_resp = serve_spa_root()
    assert isinstance(root_resp, FileResponse)
    assert root_resp.path.endswith("index.html")
    print("[PASS] serve_spa_root returns index.html FileResponse")

    # 2. Test SPA catch-all client route
    client_route_resp = serve_spa_catch_all("explore")
    assert isinstance(client_route_resp, FileResponse)
    assert client_route_resp.path.endswith("index.html")
    print("[PASS] serve_spa_catch_all('explore') returns index.html FileResponse")

    # 3. Test static asset lookup
    assets = list((static_dir / "assets").glob("*.css"))
    if assets:
        css_name = f"assets/{assets[0].name}"
        css_resp = serve_spa_catch_all(css_name)
        assert isinstance(css_resp, FileResponse)
        print(f"[PASS] Static asset {css_name} served correctly")

    # 4. Test API route 404 behavior (not masked by SPA)
    try:
        serve_spa_catch_all("api/v1/nonexistent")
        assert False, "Should have raised HTTPException 404"
    except Exception as e:
        assert getattr(e, "status_code", None) == 404
        print("[PASS] API routes (api/v1/*) correctly yield 404 rather than falling back to SPA")

    # 5. Test health check priority
    db = SessionLocal()
    try:
        health_data = health_check(db=db)
        assert health_data["status"] == "healthy"
        print("[PASS] Health check returns:", health_data)
    finally:
        db.close()

    # 6. Test root metadata
    root_meta = root()
    assert root_meta["status"] == "online"
    print("[PASS] Root metadata verified:", root_meta["app"])

    print("\nAll SPA static serving and routing tests passed successfully!")

if __name__ == "__main__":
    test_spa_serving()
