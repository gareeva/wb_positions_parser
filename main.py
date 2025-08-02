from flask import Flask, request, jsonify
import requests
import os

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
        # Начальный запрос с keyword
        params = {
            "query": keyword,
            "page": page,
            "resultset": "catalog"
        }
        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        try:
            # Поддержка вложенных preset
            for _ in range(5):  # максимум 5 перенаправлений
                res = requests.get("https://search.wb.ru/exactmatch/ru/common/v4/search", headers=headers, params=params, timeout=10)
                data = res.json()

                if "data" in data and "products" in data["data"]:
                    break  # получили выдачу

                if "query" in data and "preset=" in data["query"]:
                    preset = data["query"].split("=")[1]
                    params = {
                        "preset": preset,
                        "page": page,
                        "resultset": "catalog",
                        "query": "1"
                    }
                else:
                    return jsonify({"error": "No products and no preset redirect"}), 500

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
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
