-  Publishing 

    -  Sending messages [ Sending messages ](https://docs.ntfy.sh/publish/)

        - [ Message title ](https://docs.ntfy.sh/publish/#message-title)

        - [ Message priority ](https://docs.ntfy.sh/publish/#message-priority)

        - [ Tags & emojis 🥳 🎉 ](https://docs.ntfy.sh/publish/#tags-emojis)

        - [ Markdown formatting ](https://docs.ntfy.sh/publish/#markdown-formatting)

        - [ Click action ](https://docs.ntfy.sh/publish/#click-action)

        - [ Icons ](https://docs.ntfy.sh/publish/#icons)

        - [ Attachments ](https://docs.ntfy.sh/publish/#attachments)

            - [ Attach local file ](https://docs.ntfy.sh/publish/#attach-local-file)

            - [ Attach file from a URL ](https://docs.ntfy.sh/publish/#attach-file-from-a-url)

        - [ Action buttons ](https://docs.ntfy.sh/publish/#action-buttons)

            - [ Defining actions ](https://docs.ntfy.sh/publish/#defining-actions)

                - [ Using a header ](https://docs.ntfy.sh/publish/#using-a-header)

                - [ Using a JSON array ](https://docs.ntfy.sh/publish/#using-a-json-array)

            - [ Open website/app ](https://docs.ntfy.sh/publish/#open-websiteapp)

            - [ Send Android broadcast ](https://docs.ntfy.sh/publish/#send-android-broadcast)

            - [ Send HTTP request ](https://docs.ntfy.sh/publish/#send-http-request)

            - [ Copy to clipboard ](https://docs.ntfy.sh/publish/#copy-to-clipboard)

        - [ Scheduled delivery ](https://docs.ntfy.sh/publish/#scheduled-delivery)

            - [ Updating scheduled notifications ](https://docs.ntfy.sh/publish/#updating-scheduled-notifications)

            - [ Canceling scheduled notifications ](https://docs.ntfy.sh/publish/#canceling-scheduled-notifications)

        - [ Message templating ](https://docs.ntfy.sh/publish/#message-templating)

            - [ Pre-defined templates ](https://docs.ntfy.sh/publish/#pre-defined-templates)

            - [ Custom templates ](https://docs.ntfy.sh/publish/#custom-templates)

            - [ Inline templating ](https://docs.ntfy.sh/publish/#inline-templating)

            - [ Template syntax ](https://docs.ntfy.sh/publish/#template-syntax)

            - [ Template functions ](https://docs.ntfy.sh/publish/#template-functions)

        - [ E-mail notifications ](https://docs.ntfy.sh/publish/#e-mail-notifications)

        - [ E-mail publishing ](https://docs.ntfy.sh/publish/#e-mail-publishing)

        - [ Phone calls ](https://docs.ntfy.sh/publish/#phone-calls)

        - [ Publish as JSON ](https://docs.ntfy.sh/publish/#publish-as-json)

        - [ Webhooks (publish via GET) ](https://docs.ntfy.sh/publish/#webhooks-publish-via-get)

        - [ Updating + deleting notifications ](https://docs.ntfy.sh/publish/#updating-deleting-notifications)

            - [ Updating notifications ](https://docs.ntfy.sh/publish/#updating-notifications)

            - [ Clearing notifications ](https://docs.ntfy.sh/publish/#clearing-notifications)

            - [ Deleting notifications ](https://docs.ntfy.sh/publish/#deleting-notifications)

        - [ Authentication ](https://docs.ntfy.sh/publish/#authentication)

            - [ Username + password ](https://docs.ntfy.sh/publish/#username-password)

            - [ Access tokens ](https://docs.ntfy.sh/publish/#access-tokens)

            - [ Query param ](https://docs.ntfy.sh/publish/#query-param)

        - [ Advanced features ](https://docs.ntfy.sh/publish/#advanced-features)

            - [ Message caching ](https://docs.ntfy.sh/publish/#message-caching)

            - [ Disable Firebase ](https://docs.ntfy.sh/publish/#disable-firebase)

            - [ UnifiedPush ](https://docs.ntfy.sh/publish/#unifiedpush)

            - [ Matrix Gateway ](https://docs.ntfy.sh/publish/#matrix-gateway)

        - [ Public topics ](https://docs.ntfy.sh/publish/#public-topics)

        - [ Limitations ](https://docs.ntfy.sh/publish/#limitations)

        - [ List of all parameters ](https://docs.ntfy.sh/publish/#list-of-all-parameters)

-  Subscribing 

    - [ From your phone ](https://docs.ntfy.sh/subscribe/phone/)

    - [ From the Web app ](https://docs.ntfy.sh/subscribe/web/)

    - [ From the Desktop ](https://docs.ntfy.sh/subscribe/pwa/)

    - [ From the CLI ](https://docs.ntfy.sh/subscribe/cli/)

    - [ Using the API ](https://docs.ntfy.sh/subscribe/api/)

-  Self-hosting 

    - [ Installation ](https://docs.ntfy.sh/install/)

    - [ Configuration ](https://docs.ntfy.sh/config/)

-
    - [ FAQs ](https://docs.ntfy.sh/faq/)

    - [ Examples ](https://docs.ntfy.sh/examples/)

    - [ Integrations + projects ](https://docs.ntfy.sh/integrations/)

    - [ Release notes ](https://docs.ntfy.sh/releases/)

    - [ Emojis 🥳 🎉 ](https://docs.ntfy.sh/emojis/)

    - [ Template functions ](https://docs.ntfy.sh/publish/template-functions/)

    - [ Troubleshooting ](https://docs.ntfy.sh/troubleshooting/)

    - [ Known issues ](https://docs.ntfy.sh/known-issues/)

    - [ Deprecation notices ](https://docs.ntfy.sh/deprecations/)

    - [ Development ](https://docs.ntfy.sh/develop/)

    - [ Contributing ](https://docs.ntfy.sh/contributing/)

    - [ Privacy policy ](https://docs.ntfy.sh/privacy/)

# Publishing

Publishing messages can be done via HTTP PUT/POST or via the [ntfy CLI](https://docs.ntfy.sh/subscribe/cli/#publish-messages) ([install instructions](https://docs.ntfy.sh/install/)). Topics are created on the fly by subscribing or publishing to them. Because there is no sign-up, **the topic is essentially a password** , so pick something that's not easily guessable.

Here's an example showing how to publish a simple message using a POST request:

[Command line (curl)](https://docs.ntfy.sh/publish/#__tabbed_1_1)[ntfy CLI](https://docs.ntfy.sh/publish/#__tabbed_1_2)[HTTP](https://docs.ntfy.sh/publish/#__tabbed_1_3)[JavaScript](https://docs.ntfy.sh/publish/#__tabbed_1_4)[Go](https://docs.ntfy.sh/publish/#__tabbed_1_5)[PowerShell](https://docs.ntfy.sh/publish/#__tabbed_1_6)[Python](https://docs.ntfy.sh/publish/#__tabbed_1_7)[PHP](https://docs.ntfy.sh/publish/#__tabbed_1_8)

```
curl -d "Backup successful 😀" ntfy.sh/mytopic
```
```
ntfy publish mytopic "Backup successful 😀"
```
```
POST /mytopic HTTP/1.1
Host: ntfy.sh

Backup successful 😀
```
```
fetch('https://ntfy.sh/mytopic', {
  method: 'POST', // PUT works too
  body: 'Backup successful 😀'
})
```
```
http.Post("https://ntfy.sh/mytopic", "text/plain",
    strings.NewReader("Backup successful 😀"))
```
```
$Request = @{
  Method = "POST"
  URI = "https://ntfy.sh/mytopic"
  Body = "Backup successful"
}
Invoke-RestMethod @Request
```
```
requests.post("https://ntfy.sh/mytopic", 
    data="Backup successful 😀".encode(encoding='utf-8'))
```
```
file_get_contents('https://ntfy.sh/mytopic', false, stream_context_create([
    'http' => [
        'method' => 'POST', // PUT also works
        'header' => 'Content-Type: text/plain',
        'content' => 'Backup successful 😀'
    ]
]));
```
If you have the [Android app](https://docs.ntfy.sh/subscribe/phone/) installed on your phone, this will create a notification that looks like this:

![](https://aka.doubaocdn.com/s/0UyF1wqMjp)

Android notification

There are more features related to publishing messages: You can set a [notification priority](https://docs.ntfy.sh/publish/#message-priority), a [title](https://docs.ntfy.sh/publish/#message-title), and [tag messages](https://docs.ntfy.sh/publish/#tags-emojis) 🥳 🎉. Here's an example that uses some of them at together:

[Command line (curl)](https://docs.ntfy.sh/publish/#__tabbed_2_1)[ntfy CLI](https://docs.ntfy.sh/publish/#__tabbed_2_2)[HTTP](https://docs.ntfy.sh/publish/#__tabbed_2_3)[JavaScript](https://docs.ntfy.sh/publish/#__tabbed_2_4)[Go](https://docs.ntfy.sh/publish/#__tabbed_2_5)[PowerShell](https://docs.ntfy.sh/publish/#__tabbed_2_6)[Python](https://docs.ntfy.sh/publish/#__tabbed_2_7)[PHP](https://docs.ntfy.sh/publish/#__tabbed_2_8)

```
curl \
 -H "Title: Unauthorized access detected" \
 -H "Priority: urgent" \
 -H "Tags: warning,skull" \
 -d "Remote access to phils-laptop detected. Act right away." \
 ntfy.sh/phil_alerts
```
```
ntfy publish \
 --title "Unauthorized access detected" \
 --tags warning,skull \
 --priority urgent \
 mytopic \
 "Remote access to phils-laptop detected. Act right away."
```
```
POST /phil_alerts HTTP/1.1
Host: ntfy.sh
Title: Unauthorized access detected
Priority: urgent
Tags: warning,skull

Remote access to phils-laptop detected. Act right away.
```
```
fetch('https://ntfy.sh/phil_alerts', {
    method: 'POST', // PUT works too
    body: 'Remote access to phils-laptop detected. Act right away.',
    headers: {
        'Title': 'Unauthorized access detected',
        'Priority': 'urgent',
        'Tags': 'warning,skull'
    }
})
```
```
req, _ := http.NewRequest("POST", "https://ntfy.sh/phil_alerts",
    strings.NewReader("Remote access to phils-laptop detected. Act right away."))
req.Header.Set("Title", "Unauthorized access detected")
req.Header.Set("Priority", "urgent")
req.Header.Set("Tags", "warning,skull")
http.DefaultClient.Do(req)
```
```
$Request = @{
  Method = "POST"
  URI = "https://ntfy.sh/phil_alerts"
  Headers = @{
    Title = "Unauthorized access detected"
    Priority = "urgent"
    Tags = "warning,skull"
  }
  Body = "Remote access to phils-laptop detected. Act right away."
}
Invoke-RestMethod @Request
```
```
requests.post("https://ntfy.sh/phil_alerts",
    data="Remote access to phils-laptop detected. Act right away.",
    headers={
        "Title": "Unauthorized access detected",
        "Priority": "urgent",
        "Tags": "warning,skull"
    })
```
```
file_get_contents('https://ntfy.sh/phil_alerts', false, stream_context_create([
    'http' => [
        'method' => 'POST', // PUT also works
        'header' =>
            "Content-Type: text/plain\r\n" .
            "Title: Unauthorized access detected\r\n" .
            "Priority: urgent\r\n" .
            "Tags: warning,skull",
        'content' => 'Remote access to phils-laptop detected. Act right away.'
    ]
]));
```
![](https://aka.doubaocdn.com/s/BiPY1wqMjp)

Urgent notification with tags and title

You can also do multi-line messages. Here's an example using a [click action](https://docs.ntfy.sh/publish/#click-action), an [action button](https://docs.ntfy.sh/publish/#action-buttons), an [external image attachment](https://docs.ntfy.sh/publish/#attach-file-from-a-url) and [email publishing](https://docs.ntfy.sh/publish/#e-mail-publishing):

[Command line (curl)](https://docs.ntfy.sh/publish/#__tabbed_3_1)[ntfy CLI](https://docs.ntfy.sh/publish/#__tabbed_3_2)[HTTP](https://docs.ntfy.sh/publish/#__tabbed_3_3)[JavaScript](https://docs.ntfy.sh/publish/#__tabbed_3_4)[Go](https://docs.ntfy.sh/publish/#__tabbed_3_5)[PowerShell](https://docs.ntfy.sh/publish/#__tabbed_3_6)[Python](https://docs.ntfy.sh/publish/#__tabbed_3_7)[PHP](https://docs.ntfy.sh/publish/#__tabbed_3_8)

```
curl \
 -H "Click: https://home.nest.com/" \
 -H "Attach: https://nest.com/view/yAxkasd.jpg" \
 -H "Actions: http, Open door, https://api.nest.com/open/yAxkasd, clear=true" \
 -H "Email: phil@example.com" \
 -d "There's someone at the door. 🐶

Please check if it's a good boy or a hooman. 
Doggies have been known to ring the doorbell." \
 ntfy.sh/mydoorbell
```
```
ntfy publish \
 --click="https://home.nest.com/" \
 --attach="https://nest.com/view/yAxkasd.jpg" \
 --actions="http, Open door, https://api.nest.com/open/yAxkasd, clear=true" \
 --email="phil@example.com" \
 mydoorbell \
 "There's someone at the door. 🐶

Please check if it's a good boy or a hooman. 
Doggies have been known to ring the doorbell."
```
```
POST /mydoorbell HTTP/1.1
Host: ntfy.sh
Click: https://home.nest.com/
Attach: https://nest.com/view/yAxkasd.jpg
Actions: http, Open door, https://api.nest.com/open/yAxkasd, clear=true
Email: phil@example.com

There's someone at the door. 🐶

Please check if it's a good boy or a hooman. 
Doggies have been known to ring the doorbell.
```
```
fetch('https://ntfy.sh/mydoorbell', {
    method: 'POST', // PUT works too
    headers: {
        'Click': 'https://home.nest.com/',
        'Attach': 'https://nest.com/view/yAxkasd.jpg',
        'Actions': 'http, Open door, https://api.nest.com/open/yAxkasd, clear=true',
        'Email': 'phil@example.com'
    },
    body: `There's someone at the door. 🐶

Please check if it's a good boy or a hooman. 
Doggies have been known to ring the doorbell.`,
})
```
```
req, _ := http.NewRequest("POST", "https://ntfy.sh/mydoorbell",
    strings.NewReader(`There's someone at the door. 🐶

Please check if it's a good boy or a hooman. 
Doggies have been known to ring the doorbell.`))
req.Header.Set("Click", "https://home.nest.com/")
req.Header.Set("Attach", "https://nest.com/view/yAxkasd.jpg")
req.Header.Set("Actions", "http, Open door, https://api.nest.com/open/yAxkasd, clear=true")
req.Header.Set("Email", "phil@example.com")
http.DefaultClient.Do(req)
```
```
$Request = @{
  Method = "POST"
  URI = "https://ntfy.sh/mydoorbell"
  Headers = @{
    Click = "https://home.nest.com"
    Attach = "https://nest.com/view/yAxksd.jpg"
    Actions = "http, Open door, https://api.nest.com/open/yAxkasd, clear=true"
    Email = "phil@example.com"
  }
  Body = "There's someone at the door. 🐶`n
  `n
 Please check if it's a good boy or a hooman.`n
 Doggies have been known to ring the doorbell.`n"
}
Invoke-RestMethod @Request
```
```
requests.post("https://ntfy.sh/mydoorbell",
    data="""There's someone at the door. 🐶

Please check if it's a good boy or a hooman.
Doggies have been known to ring the doorbell.""".encode('utf-8'),
    headers={
        "Click": "https://home.nest.com/",
        "Attach": "https://nest.com/view/yAxkasd.jpg",
        "Actions": "http, Open door, https://api.nest.com/open/yAxkasd, clear=true",
        "Email": "phil@example.com"
    })
```
```
file_get_contents('https://ntfy.sh/mydoorbell', false, stream_context_create([
    'http' => [
        'method' => 'POST', // PUT also works
        'header' =>
            "Content-Type: text/plain\r\n" .
            "Click: https://home.nest.com/\r\n" .
            "Attach: https://nest.com/view/yAxkasd.jpg\r\n" .
            "Actions": "http, Open door, https://api.nest.com/open/yAxkasd, clear=true\r\n" .
            "Email": "phil@example.com\r\n",
        'content' => 'There\'s someone at the door. 🐶

Please check if it\'s a good boy or a hooman.
Doggies have been known to ring the doorbell.'
    ]
]));
```
![](https://aka.doubaocdn.com/s/ihfl1wqMjp)

Notification using a click action, a user action, with an external image attachment and forwarded via email

## Message title

*Supported on:*

The notification title is typically set to the topic short URL (e.g. `ntfy.sh/mytopic`). To override the title, you can set the `X-Title` header (or any of its aliases: `Title`, `ti`, or `t`).

[Command line (curl)](https://docs.ntfy.sh/publish/#__tabbed_4_1)[ntfy CLI](https://docs.ntfy.sh/publish/#__tabbed_4_2)[HTTP](https://docs.ntfy.sh/publish/#__tabbed_4_3)[JavaScript](https://docs.ntfy.sh/publish/#__tabbed_4_4)[Go](https://docs.ntfy.sh/publish/#__tabbed_4_5)[PowerShell](https://docs.ntfy.sh/publish/#__tabbed_4_6)[Python](https://docs.ntfy.sh/publish/#__tabbed_4_7)[PHP](https://docs.ntfy.sh/publish/#__tabbed_4_8)

```
curl -H "X-Title: Dogs are better than cats" -d "Oh my ..." ntfy.sh/controversial
curl -H "Title: Dogs are better than cats" -d "Oh my ..." ntfy.sh/controversial
curl -H "t: Dogs are better than cats" -d "Oh my ..." ntfy.sh/controversial
```
```
ntfy publish \
 -t "Dogs are better than cats" \
 controversial "Oh my ..."
```
```
POST /controversial HTTP/1.1
Host: ntfy.sh
Title: Dogs are better than cats

Oh my ...
```
```
fetch('https://ntfy.sh/controversial', {
    method: 'POST',
    body: 'Oh my ...',
    headers: { 'Title': 'Dogs are better than cats' }
})
```
```
req, _ := http.NewRequest("POST", "https://ntfy.sh/controversial", strings.NewReader("Oh my ..."))
req.Header.Set("Title", "Dogs are better than cats")
http.DefaultClient.Do(req)
```
```
$Request = @{
  Method = "POST"
  URI = "https://ntfy.sh/controversial"
  Headers = @{
    Title = "Dogs are better than cats"
  }
  Body = "Oh my ..."
}
Invoke-RestMethod @Request
```
```
requests.post("https://ntfy.sh/controversial",
    data="Oh my ...",
    headers={ "Title": "Dogs are better than cats" })
```
```
file_get_contents('https://ntfy.sh/controversial', false, stream_context_create([
    'http' => [
        'method' => 'POST',
        'header' =>
            "Content-Type: text/plain\r\n" .
            "Title: Dogs are better than cats",
        'content' => 'Oh my ...'
    ]
]));
```
![](https://aka.doubaocdn.com/s/Mvxe1wqMjp)

Detail view of notification with title

Info

ntfy supports UTF-8 in HTTP headers, but [not every library or programming language does](https://www.jmix.io/blog/utf-8-in-http-headers/). If non-ASCII characters are causing issues for you in the title (i.e. you're seeing `?` symbols), you may also encode any header (including the title) as [RFC 2047](https://datatracker.ietf.org/doc/html/rfc2047#section-2), e.g. `=?UTF-8?B?8J+HqfCfh6o=?=` ([base64](https://en.wikipedia.org/wiki/Base64)), or `=?UTF-8?Q?=C3=84pfel?=` ([quoted-printable](https://en.wikipedia.org/wiki/Quoted-printable)).

## Message priority

*Supported on:*

All messages have a priority, which defines how urgently your phone notifies you. On Android, you can set custom notification sounds and vibration patterns on your phone to map to these priorities (see [Android config](https://docs.ntfy.sh/subscribe/phone/)).

The following priorities exist:

| Priority | Icon | ID | Name | Description |
|---|---|---|---|---|
| Max priority |  | `5` | `max`/`urgent` | Really long vibration bursts, default notification sound with a pop-over notification. |
| High priority |  | `4` | `high` | Long vibration burst, default notification sound with a pop-over notification. |
| **Default priority** | *(none)* | `3` | `default` | Short default vibration and sound. Default notification behavior. |
| Low priority |  | `2` | `low` | No vibration or sound. Notification will not visibly show up until notification drawer is pulled down. |
| Min priority |  | `1` | `min` | No vibration or sound. The notification will be under the fold in "Other notifications". |

You can set the priority with the header `X-Priority` (or any of its aliases: `Priority`, `prio`, or `p`).

[Command line (curl)](https://docs.ntfy.sh/publish/#__tabbed_5_1)[ntfy CLI](https://docs.ntfy.sh/publish/#__tabbed_5_2)[HTTP](https://docs.ntfy.sh/publish/#__tabbed_5_3)[JavaScript](https://docs.ntfy.sh/publish/#__tabbed_5_4)[Go](https://docs.ntfy.sh/publish/#__tabbed_5_5)[PowerShell](https://docs.ntfy.sh/publish/#__tabbed_5_6)[Python](https://docs.ntfy.sh/publish/#__tabbed_5_7)[PHP](https://docs.ntfy.sh/publish/#__tabbed_5_8)

```
curl -H "X-Priority: 5" -d "An urgent message" ntfy.sh/phil_alerts
curl -H "Priority: low" -d "Low priority message" ntfy.sh/phil_alerts
curl -H p:4 -d "A high priority message" ntfy.sh/phil_alerts
```
```
ntfy publish \ 
 -p 5 \
 phil_alerts An urgent message
```
```
POST /phil_alerts HTTP/1.1
Host: ntfy.sh
Priority: 5

An urgent message
```
```
fetch('https://ntfy.sh/phil_alerts', {
    method: 'POST',
    body: 'An urgent message',
    headers: { 'Priority': '5' }
})
```
```
req, _ := http.NewRequest("POST", "https://ntfy.sh/phil_alerts", strings.NewReader("An urgent message"))
req.Header.Set("Priority", "5")
http.DefaultClient.Do(req)
```
```
$Request = @{
  Method = 'POST'
  URI = "https://ntfy.sh/phil_alerts"
  Headers = @{
    Priority = "5"
  }
  Body = "An urgent message"
}
Invoke-RestMethod @Request
```
```
