from pathlib import Path
from typing import Any, Dict, Iterable, List


def build_report(
    posts: List[Dict[str, Any]],
    comments: List[Dict[str, Any]],
    generated_posts: List[Dict[str, Any]],
    generated_comments: Iterable[Dict[str, Any]],
    dist_root: Path,
) -> Dict[str, Any]:
    post_ids = {post["id"] for post in posts}
    generated_post_ids = {post["id"] for post in generated_posts}
    generated_comments = list(generated_comments)
    media = [item for post in posts for item in post.get("media", [])]
    generated_media = [item for post in generated_posts for item in post.get("media", [])]
    expected_pages = [dist_root / "blog" / f"{post['slug']}.html" for post in generated_posts]

    report = {
        "posts_parsed": len(posts),
        "posts_public": sum(post["visibility"] == "public" for post in posts),
        "posts_private_or_draft": sum(post["visibility"] != "public" for post in posts),
        "posts_generated": len(generated_posts),
        "comments_parsed": len(comments),
        "comments_public": sum(comment["visibility"] == "public" for comment in comments),
        "comments_hidden": sum(comment["visibility"] != "public" for comment in comments),
        "comments_on_generated_posts": len(generated_comments),
        "comments_generated": len(generated_comments),
        "orphan_comments": sum(comment["post_id"] not in post_ids for comment in comments),
        "article_image_references": len(media),
        "article_images_available": sum(bool(item.get("available")) for item in media),
        "missing_images": sum(not item.get("available") for item in media),
        "generated_article_image_references": len(generated_media),
        "generated_missing_images": sum(not item.get("available") for item in generated_media),
        "missing_generated_pages": sum(not path.exists() for path in expected_pages),
    }
    report["build_success"] = (
        report["orphan_comments"] == 0
        and report["missing_generated_pages"] == 0
        and all(comment["post_id"] in generated_post_ids for comment in generated_comments)
    )
    return report

