## coding=utf-8
<%!
    from datetime import datetime
%>

<div class="header">

    <h1>${story.title}</h1>

    by

    <h2>${story.author}</h2>

</div>


<div class="titlepage">

    <div><strong>Story:</strong> ${story.title}</div>

    <div><strong>Author:</strong> ${story.author}</div>


    <div><strong>URL:</strong> <a href="${story.main_url}">${story.main_url}</a></div>

    <div><strong>Author URL:</strong> <a href="${story.author_url}">${story.author_url}</a></div>

    <div><strong>Rating:</strong> ${story.rating}</div>

    <div><strong>Category:</strong> ${story.category}</div>

    <div><strong>Genre:</strong> ${story.genre}</div>

    <div><strong>Published:</strong> ${story.published.isoformat()}</div>

    <div><strong>Updated:</strong> ${story.updated.isoformat()}</div>

    <div><strong>Downloaded:</strong> ${datetime.now()}</div>

    <div><strong>Words:</strong> ${story.words}</div>

    <div><strong>Chapters:</strong> ${len(story.chapters)}/${len(story.chapters) if story.complete else "??"}</div>

    <div><strong>Summary:</strong>

        <p>${story.summary}</p>

    </div>

</div>
