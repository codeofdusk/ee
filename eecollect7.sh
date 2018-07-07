#!/bin/bash
sql enwiki -e "select page_title, rev_timestamp, page_namespace from page, revision where page_id>8000000 and page_id<10000000 and rev_parent_id=0 and rev_page = page_id and (page_namespace=0 or page_namespace=1);"
