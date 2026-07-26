- [Telegram Bots](https://core.telegram.org/bots)

- [Telegram Bot API](https://core.telegram.org/bots/api)

# Telegram Bot API

The Bot API is an HTTP-based interface created for developers keen on building bots for Telegram.

To learn how to create and set up a bot, please consult our [**Introduction to Bots** ](https://core.telegram.org/bots) and [**Bot FAQ** ](https://core.telegram.org/bots/faq).

### 
Recent changes

Subscribe to [@BotNews](https://t.me/botnews) to be the first to know about the latest updates and join the discussion in [@BotTalk](https://t.me/bottalk)

#### 
May 8, 2026

**Bot API 10.0**

**Guest Mode**

- Introduced support for [guest mode](https://core.telegram.org/bots/features#guest-bots), allowing bots to receive certain messages and issue replies within chats they are not a member of.

- Added the field *supports_guest_queries* to the class [User](https://core.telegram.org/bots/api#user).

- Added the fields *guest_bot_caller_user* and *guest_bot_caller_chat* to the class [Message](https://core.telegram.org/bots/api#message).

- Added the field *guest_query_id* to the class [Message](https://core.telegram.org/bots/api#message).

- Added the field *guest_message* to the class [Update](https://core.telegram.org/bots/api#update).

- Added the class [SentGuestMessage](https://core.telegram.org/bots/api#sentguestmessage) and the method [answerGuestQuery](https://core.telegram.org/bots/api#answerguestquery).

**Chat Management**

- Added the field *can_react_to_messages* to the classes [ChatMemberRestricted](https://core.telegram.org/bots/api#chatmemberrestricted) and [ChatPermissions](https://core.telegram.org/bots/api#chatpermissions).

- Added the parameter *return_bots* to the method [getChatAdministrators](https://core.telegram.org/bots/api#getchatadministrators).

- Added the method [deleteAllMessageReactions](https://core.telegram.org/bots/api#deleteallmessagereactions).

- Added the method [deleteMessageReaction](https://core.telegram.org/bots/api#deletemessagereaction).

- Added the ability to see certain messages sent by other bots in groups.

**Polls**

- Added the classes [InputMediaSticker](https://core.telegram.org/bots/api#inputmediasticker), [InputMediaLocation](https://core.telegram.org/bots/api#inputmedialocation), and [InputMediaVenue](https://core.telegram.org/bots/api#inputmediavenue).

- Added the class [PollMedia](https://core.telegram.org/bots/api#pollmedia), representing a media in a poll.

- Added the field *media* to the class [Poll](https://core.telegram.org/bots/api#poll), allowing bots to see media in polls.

- Added the field *explanation_media* to the class [Poll](https://core.telegram.org/bots/api#poll), allowing bots to see media in quiz explanations.

- Added the field *media* to the class [PollOption](https://core.telegram.org/bots/api#polloption), allowing bots to see media in poll options.

- Added the class [InputPollMedia](https://core.telegram.org/bots/api#inputpollmedia) and the parameters *media* and *explanation_media* to the method [sendPoll](https://core.telegram.org/bots/api#sendpoll), allowing bots to add media to polls.

- Added the class [InputPollOptionMedia](https://core.telegram.org/bots/api#inputpolloptionmedia) and the field *media* to the class [InputPollOption](https://core.telegram.org/bots/api#inputpolloption), allowing bots to add media to poll options.

- Added the field *members_only* to the class [Poll](https://core.telegram.org/bots/api#poll).

- Added the parameter *members_only* to the method [sendPoll](https://core.telegram.org/bots/api#sendpoll).

- Added the field *country_codes* to the class [Poll](https://core.telegram.org/bots/api#poll).

- Added the parameter *country_codes* to the method [sendPoll](https://core.telegram.org/bots/api#sendpoll).

- Decreased the minimum number of poll options from 2 to 1.

**Live photos**

- Added the class [LivePhoto](https://core.telegram.org/bots/api#livephoto), which represents a photo with a short video.

- Added the class [InputMediaLivePhoto](https://core.telegram.org/bots/api#inputmedialivephoto).

- Added the field *live_photo* to the classes [Message](https://core.telegram.org/bots/api#message) and [ExternalReplyInfo](https://core.telegram.org/bots/api#externalreplyinfo).

- Added the method [sendLivePhoto](https://core.telegram.org/bots/api#sendlivephoto), allowing bots to send live photos.

- Added the class [PaidMediaLivePhoto](https://core.telegram.org/bots/api#paidmedialivephoto), which describes a paid media with a live photo.

- Added the class [InputPaidMediaLivePhoto](https://core.telegram.org/bots/api#inputpaidmedialivephoto), allowing bots to send live photos as paid media.

- Allowed to use live photos in [sendMediaGroup](https://core.telegram.org/bots/api#sendmediagroup) and [editMessageMedia](https://core.telegram.org/bots/api#editmessagemedia),

**General**

- Allowed [Secretary Bots](https://core.telegram.org/bots/features#secretary-bots) to manage accounts of users without a Telegram Premium subscription.

- Added the ability to send messages to other bots via username if both bots enabled bot-to-bot communication.

- Added the ability to reply to other bots from a business bot if the business bot enabled bot-to-bot communication.

- Allowed bots to pass an empty text in the method [sendMessageDraft](https://core.telegram.org/bots/api#sendmessagedraft).

- Added the class [BotAccessSettings](https://core.telegram.org/bots/api#botaccesssettings) and the method [getManagedBotAccessSettings](https://core.telegram.org/bots/api#getmanagedbotaccesssettings).

- Added the method [setManagedBotAccessSettings](https://core.telegram.org/bots/api#setmanagedbotaccesssettings).

- Added the method [getUserPersonalChatMessages](https://core.telegram.org/bots/api#getuserpersonalchatmessages).

#### 
April 3, 2026

**Bot API 9.6**

**Managed Bots**

- Added the field *can_manage_bots* to the class [User](https://core.telegram.org/bots/api#user).

- Added the class [KeyboardButtonRequestManagedBot](https://core.telegram.org/bots/api#keyboardbuttonrequestmanagedbot) and the field *request_managed_bot* to the class [KeyboardButton](https://core.telegram.org/bots/api#keyboardbutton).

- Added the class [ManagedBotCreated](https://core.telegram.org/bots/api#managedbotcreated) and the field *managed_bot_created* to the class [Message](https://core.telegram.org/bots/api#message).

- Added updates about the creation of managed bots and the change of their token, represented by the class [ManagedBotUpdated](https://core.telegram.org/bots/api#managedbotupdated) and the field *managed_bot* in the class [Update](https://core.telegram.org/bots/api#update).

- Added the methods [getManagedBotToken](https://core.telegram.org/bots/api#getmanagedbottoken) and [replaceManagedBotToken](https://core.telegram.org/bots/api#replacemanagedbottoken).

- Added the class [PreparedKeyboardButton](https://core.telegram.org/bots/api#preparedkeyboardbutton) and the method [savePreparedKeyboardButton](https://core.telegram.org/bots/api#savepreparedkeyboardbutton), allowing bots to request users, chats and managed bots from Mini Apps.

- Added the method *requestChat* to the class [WebApp](https://core.telegram.org/bots/webapps#initializing-mini-apps).

- Added support for `https://t.me/newbot/{manager_bot_username}/{suggested_bot_username}[?name={suggested_bot_name}]` links, allowing bots to request the creation of a managed bot via a link.

**Polls**

- Added support for quizzes with multiple correct answers.

- Replaced the field *correct_option_id* with the field *correct_option_ids* in the class [Poll](https://core.telegram.org/bots/api#poll).

- Replaced the parameter *correct_option_id* with the parameter *correct_option_ids* in the method [sendPoll](https://core.telegram.org/bots/api#sendpoll).

- Allowed to pass *allows_multiple_answers* for quizzes in the method [sendPoll](https://core.telegram.org/bots/api#sendpoll).

- Increased the maximum time for automatic poll closure to 2628000 seconds.

- Added the field *allows_revoting* to the class [Poll](https://core.telegram.org/bots/api#poll).

- Added the parameter *allows_revoting* to the method [sendPoll](https://core.telegram.org/bots/api#sendpoll).

- Added the parameter *shuffle_options* to the method [sendPoll](https://core.telegram.org/bots/api#sendpoll).

- Added the parameter *allow_adding_options* to the method [sendPoll](https://core.telegram.org/bots/api#sendpoll).

- Added the parameter *hide_results_until_closes* to the method [sendPoll](https://core.telegram.org/bots/api#sendpoll).

- Added the fields *description* and *description_entities* to the class [Poll](https://core.telegram.org/bots/api#poll).

- Added the parameters *description*, *description_parse_mode*, and *description_entities* to the method [sendPoll](https://core.telegram.org/bots/api#sendpoll).

- Added the field *persistent_id* to the class [PollOption](https://core.telegram.org/bots/api#polloption), representing a persistent identifier for the option.

- Added the field *option_persistent_ids* to the class [PollAnswer](https://core.telegram.org/bots/api#pollanswer).

- Added the fields *added_by_user* and *added_by_chat* to the class [PollOption](https://core.telegram.org/bots/api#polloption), denoting the user and the chat which added the option.

- Added the field *addition_date* to the class [PollOption](https://core.telegram.org/bots/api#polloption), describing the date when the option was added.

- Added the class [PollOptionAdded](https://core.telegram.org/bots/api#polloptionadded) and the field *poll_option_added* to the class [Message](https://core.telegram.org/bots/api#message).

- Added the class [PollOptionDeleted](https://core.telegram.org/bots/api#polloptiondeleted) and the field *poll_option_deleted* to the class [Message](https://core.telegram.org/bots/api#message).

- Added the field *poll_option_id* to the class [ReplyParameters](https://core.telegram.org/bots/api#replyparameters), allowing bots to reply to a specific poll option.

- Added the field *reply_to_poll_option_id* to the class [Message](https://core.telegram.org/bots/api#message).

- Allowed “date_time” entities in [checklist](https://core.telegram.org/bots/api#inputchecklist) title, [checklist task](https://core.telegram.org/bots/api#inputchecklisttask) text, [TextQuote](https://core.telegram.org/bots/api#textquote), [ReplyParameters](https://core.telegram.org/bots/api#replyparameters) quote, [sendGift](https://core.telegram.org/bots/api#sendgift), and [giftPremiumSubscription](https://core.telegram.org/bots/api#giftpremiumsubscription).

#### 
March 1, 2026

**Bot API 9.5**

- Added the [MessageEntity](https://core.telegram.org/bots/api#messageentity) type “date_time”, allowing bots to show a formatted date and time to the user.

- Allowed all bots to use the method [sendMessageDraft](https://core.telegram.org/bots/api#sendmessagedraft).

- Added the field *tag* to the classes [ChatMemberMember](https://core.telegram.org/bots/api#chatmembermember) and [ChatMemberRestricted](https://core.telegram.org/bots/api#chatmemberrestricted).

- Added the method [setChatMemberTag](https://core.telegram.org/bots/api#setchatmembertag).

- Added the field *can_edit_tag* to the classes [ChatMemberRestricted](https://core.telegram.org/bots/api#chatmemberrestricted) and [ChatPermissions](https://core.telegram.org/bots/api#chatpermissions).

- Added the field *can_manage_tags* to the classes [ChatMemberAdministrator](https://core.telegram.org/bots/api#chatmemberadministrator) and [ChatAdministratorRights](https://core.telegram.org/bots/api#chatadministratorrights).

- Added the parameter *can_manage_tags* to the method [promoteChatMember](https://core.telegram.org/bots/api#promotechatmember).

- Added the field *sender_tag* to the class [Message](https://core.telegram.org/bots/api#message).

- Added the field *iconCustomEmojiId* to the class [BottomButton](https://core.telegram.org/bots/webapps#bottombutton).

#### 
February 9, 2026

**Bot API 9.4**

- Allowed bots to use custom emoji in messages directly sent by the bot to private, group and supergroup chats if the owner of the bot has a Telegram Premium subscription.

- Allowed bots to create topics in private chats using the method [createForumTopic](https://core.telegram.org/bots/api#createforumtopic).

- Allowed bots to prevent users from creating and deleting topics in private chats through a new setting in the [@BotFather](https://t.me/BotFather) Mini App.

- Added the field *allows_users_to_create_topics* to the class [User](https://core.telegram.org/bots/api#user).

- Added the field *icon_custom_emoji_id* to the classes [KeyboardButton](https://core.telegram.org/bots/api#keyboardbutton) and [InlineKeyboardButton](https://core.telegram.org/bots/api#inlinekeyboardbutton), allowing bots to show a custom emoji on buttons if they are able to use custom emoji in the message.

- Added the field *style* to the classes [KeyboardButton](https://core.telegram.org/bots/api#keyboardbutton) and [InlineKeyboardButton](https://core.telegram.org/bots/api#inlinekeyboardbutton), allowing bots to change the color of buttons.

- Added the class [ChatOwnerLeft](https://core.telegram.org/bots/api#chatownerleft) and the field *chat_owner_left* to the class [Message](https://core.telegram.org/bots/api#message).

- Added the class [ChatOwnerChanged](https://core.telegram.org/bots/api#chatownerchanged) and the field *chat_owner_changed* to the class [Message](https://core.telegram.org/bots/api#message).

- Added the methods [setMyProfilePhoto](https://core.telegram.org/bots/api#setmyprofilephoto) and [removeMyProfilePhoto](https://core.telegram.org/bots/api#removemyprofilephoto), allowing bots to manage their profile picture.

- Added the class [VideoQuality](https://core.telegram.org/bots/api#videoquality) and the field *qualities* to the class [Video](https://core.telegram.org/bots/api#video) allowing bots to get information about other available qualities of a video.

- Added the field *first_profile_audio* to the class [ChatFullInfo](https://core.telegram.org/bots/api#chatfullinfo).

- Added the class [UserProfileAudios](https://core.telegram.org/bots/api#userprofileaudios) and the method [getUserProfileAudios](https://core.telegram.org/bots/api#getuserprofileaudios), allowing bots to fetch a list of audios added to the profile of a user.

- Added the field *rarity* to the class [UniqueGiftModel](https://core.telegram.org/bots/api#uniquegiftmodel).

- Added the field *is_burned* to the class [UniqueGift](https://core.telegram.org/bots/api#uniquegift).

[**See earlier changes »**](https://core.telegram.org/bots/api-changelog)

### 
Authorizing your bot

Each bot is given a unique authentication token [when it is created](https://core.telegram.org/bots/features#botfather). The token looks something like `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`, but we'll use simply **<token>**  in this document instead. You can learn about obtaining tokens and generating new ones in [this document](https://core.telegram.org/bots/features#botfather).

### 
Making requests

All queries to the Telegram Bot API must be served over HTTPS and need to be presented in this form: `https://api.telegram.org/bot<token>/METHOD_NAME`. Like this for example:

```
https://api.telegram.org/bot123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11/getMe
```
We support **GET**  and **POST**  HTTP methods. We support four ways of passing parameters in Bot API requests:

- [URL query string](https://en.wikipedia.org/wiki/Query_string)

- application/x-www-form-urlencoded

- application/json (except for uploading files)

- multipart/form-data (use to upload files)

The response contains a JSON object, which always has a Boolean field 'ok' and may have an optional String field 'description' with a human-readable description of the result. If 'ok' equals *True*, the request was successful and the result of the query can be found in the 'result' field. In case of an unsuccessful request, 'ok' equals false and the error is explained in the 'description'. An Integer 'error_code' field is also returned, but its contents are subject to change in the future. Some errors may also have an optional field 'parameters' of the type [ResponseParameters](https://core.telegram.org/bots/api#responseparameters), which can help to automatically handle the error.

- All methods in the Bot API are case-insensitive.

- All queries must be made using UTF-8.

#### 
Making requests when getting updates

If you're using [**webhooks** ](https://core.telegram.org/bots/api#getting-updates), you can perform a request to the Bot API while sending an answer to the webhook. Use either *application/json* or *application/x-www-form-urlencoded* or *multipart/form-data* response content type for passing parameters. Specify the method to be invoked in the *method* parameter of the request. It's not possible to know that such a request was successful or get its result.

Please see our [FAQ](https://core.telegram.org/bots/faq#how-can-i-make-requests-in-response-to-updates) for examples.

### 
Using a Local Bot API Server

The Bot API server source code is available at [telegram-bot-api](https://github.com/tdlib/telegram-bot-api). You can run it locally and send the requests to your own server instead of `https://api.telegram.org`. If you switch to a local Bot API server, your bot will be able to:

- Download files without a size limit.

- Upload files up to 2000 MB.

- Upload files using their local path and [the file URI scheme](https://en.wikipedia.org/wiki/File_URI_scheme).

- Use an HTTP URL for the webhook.

- Use any local IP address for the webhook.

- Use any port for the webhook.

- Set *max_webhook_connections* up to 100000.

- Receive the absolute local path as a value of the *file_path* field without the need to download the file after a [getFile](https://core.telegram.org/bots/api#getfile) request.

#### 
Do I need a Local Bot API Server

The majority of bots will be OK with the default configuration, running on our servers. But if you feel that you need one of [these features](https://core.telegram.org/bots/api#using-a-local-bot-api-server), you're welcome to switch to your own at any time.

### 
Getting updates

There are two mutually exclusive ways of receiving updates for your bot - the [getUpdates](https://core.telegram.org/bots/api#getupdates) method on one hand and [webhooks](https://core.telegram.org/bots/api#setwebhook) on the other. Incoming updates are stored on the server until the bot receives them either way, but they will not be kept longer than 24 hours.

Regardless of which option you choose, you will receive JSON-serialized [Update](https://core.telegram.org/bots/api#update) objects as a result.

#### 
Update

This [object](https://core.telegram.org/bots/api#available-types) represents an incoming update.

At most **one**  of the optional fields can be present in any given update.

| Field | Type | Description |
|---|---|---|
| update_id | Integer | The update's unique identifier. Update identifiers start from a certain positive number and increase sequentially. This identifier becomes especially handy if you're using [webhooks](https://core.telegram.org/bots/api#setwebhook), since it allows you to ignore repeated updates or to restore the correct update sequence, should they get out of order. If there are no new updates for at least a week, then identifier of the next update will be chosen randomly instead of sequentially. |
| message | [Message](https://core.telegram.org/bots/api#message) | *Optional*. New incoming message of any kind - text, photo, sticker, etc. |
| edited_message | [Message](https://core.telegram.org/bots/api#message) | *Optional*. New version of a message that is known to the bot and was edited. This update may at times be triggered by changes to message fields that are either unavailable or not actively used by your bot. |
| channel_post | [Message](https://core.telegram.org/bots/api#message) | *Optional*. New incoming channel post of any kind - text, photo, sticker, etc. |
| edited_channel_post | [Message](https://core.telegram.org/bots/api#message) | *Optional*. New version of a channel post that is known to the bot and was edited. This update may at times be triggered by changes to message fields that are either unavailable or not actively used by your bot. |
| business_connection | [BusinessConnection](https://core.telegram.org/bots/api#businessconnection) | *Optional*. The bot was connected to or disconnected from a business account, or a user edited an existing connection with the bot |
| business_message | [Message](https://core.telegram.org/bots/api#message) | *Optional*. New message from a connected business account |
| edited_business_message | [Message](https://core.telegram.org/bots/api#message) | *Optional*. New version of a message from a connected business account |
| deleted_business_messages | [BusinessMessagesDeleted](https://core.telegram.org/bots/api#businessmessagesdeleted) | *Optional*. Messages were deleted from a connected business account |
| guest_message | [Message](https://core.telegram.org/bots/api#message) | *Optional*. New guest message. The bot can use the field *Message.guest_query_id* and the method [answerGuestQuery](https://core.telegram.org/bots/api#answerguestquery) to send a message in response. |
| message_reaction | [MessageReactionUpdated](https://core.telegram.org/bots/api#messagereactionupdated) | *Optional*. A reaction to a message was changed by a user. The bot must be an administrator in the chat and must explicitly specify `"message_reaction"` in the list of *allowed_updates* to receive these updates. The update isn't received for reactions set by bots. |
| message_reaction_count | [MessageReactionCountUpdated](https://core.telegram.org/bots/api#messagereactioncountupdated) | *Optional*. Reactions to a message with anonymous reactions were changed. The bot must be an administrator in the chat and must explicitly specify `"message_reaction_count"` in the list of *allowed_updates* to receive these updates. The updates are grouped and can be sent with delay up to a few minutes. |
| inline_query | [InlineQuery](https://core.telegram.org/bots/api#inlinequery) | *Optional*. New incoming [inline](https://core.telegram.org/bots/api#inline-mode) query |
| chosen_inline_result | [ChosenInlineResult](https://core.telegram.org/bots/api#choseninlineresult) | *Optional*. The result of an [inline](https://core.telegram.org/bots/api#inline-mode) query that was chosen by a user and sent to their chat partner. Please see our documentation on the [feedback collecting](https://core.telegram.org/bots/inline#collecting-feedback) for details on how to enable these updates for your bot. |
| callback_query | [CallbackQuery](https://core.telegram.org/bots/api#callbackquery) | *Optional*. New incoming callback query |
| shipping_query | [ShippingQuery](https://core.telegram.org/bots/api#shippingquery) | *Optional*. New incoming shipping query. Only for invoices with flexible price. |
| pre_checkout_query | [PreCheckoutQuery](https://core.telegram.org/bots/api#precheckoutquery) | *Optional*. New incoming pre-checkout query. Contains full information about checkout. |
| purchased_paid_media | [PaidMediaPurchased](https://core.telegram.org/bots/api#paidmediapurchased) | *Optional*. A user purchased paid media with a non-empty payload sent by the bot in a non-channel chat |
| poll | [Poll](https://core.telegram.org/bots/api#poll) | *Optional*. New poll state. Bots receive only updates about manually stopped polls and polls, which are sent by the bot. |
| poll_answer | [PollAnswer](https://core.telegram.org/bots/api#pollanswer) | *Optional*. A user changed their answer in a non-anonymous poll. Bots receive new votes only in polls that were sent by the bot itself. |
| my_chat_member | [ChatMemberUpdated](https://core.telegram.org/bots/api#chatmemberupdated) | *Optional*. The bot's chat member status was updated in a chat. For private chats,