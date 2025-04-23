<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GuRuTuX - Index</title> {# Or use {{ site.title }} or similar #}
    {# Link to your CSS file here for styling #}
    {# <link rel="stylesheet" href="/assets/css/style.css"> #}
    <style>
        /* Basic styling to prevent complete chaos - Replace with proper CSS file */
        body { font-family: sans-serif; line-height: 1.6; margin: 2em; }
        article { border-bottom: 1px solid #eee; margin-bottom: 2em; padding-bottom: 1em; }
        h2 { margin-bottom: 0.2em; }
        time { color: #666; font-size: 0.9em; display: block; margin-bottom: 0.5em; }
        article div { margin-bottom: 1em; } /* Space between excerpt and 'Read More' */
    </style>
</head>
<body>

    <header>
        <h1>GuRuTuX</h1> {# Or perhaps {{ site.title }} #}
        {# Optional: Navigation, description {{ site.description }} #}
    </header>

    <main>
        {% comment %} 
          Loop through posts. 
          If you ever have more than ~10-15 posts, pagination is REQUIRED. 
          This loop assumes few posts or pagination is handled elsewhere (unlikely if this is the *only* page).
        {% endcomment %}
        {% assign posts_to_show = site.posts %} {# Define variable for clarity #}
        
        {% if posts_to_show.size > 0 %}
            {% for post in posts_to_show %}
              <article>
                <h2>
                  <a href="{{ post.url | relative_url }}">
                    {{ post.title | escape }}
                  </a>
                </h2>
                <time datetime="{{ post.date | date_to_xmlschema }}">{{ post.date | date: "%B %-d, %Y" }}</time>

                <div> {# Container for the excerpt #}
                  {{ post.excerpt }}
                </div>

                {# Add 'Read More' link only if excerpt exists and is shorter than full content #}
                {% if post.excerpt != post.content %}
                    <p>
                      <a href="{{ post.url | relative_url }}">Read More &raquo;</a>
                    </p>
                {% endif %}
              </article>
            {% endfor %}
        {% else %}
            <p>No posts found.</p> {# Handle case where there are no posts #}
        {% endif %}
    </main>

    <footer>
        {# Optional footer content #}
        <p>&copy; {{ site.time | date: '%Y' }} GuRuTuX</p> {# Or your name/site name #}
    </footer>

</body>
</html>
