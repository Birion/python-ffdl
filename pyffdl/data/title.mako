## coding=utf-8
<%
    number_of_chapters = len(story._chapters) if story._complete else "??"
    chapters = "{}/{}".format(len(story._chapters), number_of_chapters)
    genres = "/".join(story._genres) if story._genres else None
    tags = ", ".join(story._tags) if story._tags else None
    characters = None
    if story._characters:
        characters = ""
        if story._characters["couples"]:
            couples = ["[" + ", ".join(x) + "]" for x in story._characters["couples"]]
            characters += " ".join(couples)
            if story._characters["singles"]:
                characters += " "
        if story._characters["singles"]:
            characters += ", ".join(story._characters["singles"])

    metadata = [
        ("Story", story._title, "title"),
        ("Author", story._author.name, "author"),
        ("URL", story.url, "story-url", True),
        ("Author URL", story._author.url, "author-url", True),
        ("Language", story._language, "lang"),
        ("Rating", story._rating, "rating"),
        ("Category", story._category, "category"),
        ("Genre", genres, "genres"),
        ("Characters", characters, "characters"),
        ("Published", story._published.to_iso8601_string() if story._published else None, "published"),
        ("Updated", story._updated.to_iso8601_string() if story._updated else None, "updated"),
        ("Downloaded", story._downloaded.to_iso8601_string(), "downloaded"),
        ("Words", story._words, "words"),
        ("Tags", tags, "tags"),
        ("Chapters", chapters, "chapters")
    ]
%>
<%def name="is_url(data, url)">
    % if url:
        <a href="${data}">${data}</a>
    %else:
        ${data}
    % endif
</%def>
<%def name="print_metadata(datatype, data, id, url=False)">
    % if data:
        <div id="${id}"><strong>${datatype}:</strong> ${is_url(data, url)}</div>
    % endif
</%def>
<div class="header">
    <h1>${story._title}</h1> by <h2>${story._author.name}</h2>
</div>
<div class="titlepage">
    % for data in metadata:
        % if data[1]:
            ${print_metadata(*data)}
        % endif
    % endfor
    % if story._summary:
        <div>
            <strong>Summary:</strong>
            <p>${story._summary}</p>
        </div>
    % endif
</div>
