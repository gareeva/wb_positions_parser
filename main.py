from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route('/check_wb_position', methods=['GET'])
def check_wb_position():
    keyword = request.args.get('keyword')
    article = request.args.get('article')

    if not keyword or not article:
        return jsonify({"error": "Missing 'keyword' or 'article' parameter"}), 400

    try:
        article = int(article)
    except ValueError:
        return jsonify({"error": "Invalid article ID"}), 400

    max_pages = 40
    position_global = 0

    for page in range(1, max_pages + 1):
        search_url = "https://search.wb.ru/exactmatch/ru/common/v4/search"
        params = {
            "query": keyword,
            "page": page
        }
        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        try:
            res = requests.get(search_url, headers=headers, params=params, timeout=10)
            if res.status_code != 200:
                return jsonify({"error": f"Wildberries API error (page {page})", "status": res.status_code}), 502

            data = res.json()
            products = data.get("data", {}).get("products", [])
            ids = [p["id"] for p in products]

            if not ids:
                break

            if article in ids:
                local_index = ids.index(article)
                global_position = position_global + local_index + 1
                return jsonify({
                    "found": True,
                    "article": article,
                    "keyword": keyword,
                    "page": page,
                    "position_on_page": local_index + 1,
                    "global_position": global_position
                })

            position_global += len(ids)

        except Exception as e:
            return jsonify({"error": f"Exception occurred: {str(e)}"}), 500

    return jsonify({
        "found": False,
        "article": article,
        "keyword": keyword,
        "message": f"Not found in top {max_pages} pages"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
