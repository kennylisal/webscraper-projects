import csv
def write_csv_report(page_datas : dict, filename="report.csv"):
    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["page_url", "category", "file_name", "link", "magnet_link", "size", "date", 'seeders', 'leechers', 'completed_download']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames,delimiter=";")

        writer.writeheader()
        for key, values in  page_datas.items():
            for value in values:
                writer.writerow({
                    "page_url": key,
                    "category": value.get("category", ""),
                    "file_name": value.get("file_name", ""),
                    "link": value.get("link", ""),
                    "magnet_link": value.get("magnet_link", ""),
                    "size": value.get("size", ""),
                    "date": value.get("date", ""),
                    "seeders": value.get("seeders", 0),
                    "leechers": value.get("leechers", 0),
                    "completed_download": value.get("completed_download", 0)
                })
