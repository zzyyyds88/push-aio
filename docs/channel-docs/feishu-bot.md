# Custom bot usage guide

Last updated on 2025-03-27

# Custom bot usage guide

A custom bot is a bot that can only be used in the current group chat. This type of robot can complete the message push by calling the webhook address in the current group chat without being reviewed by the tenant administrator. This article mainly introduces how to use custom robots.

## Precautions

- Custom bot can only be used in the current group chat. The same custom bot cannot be added to other group chats.

- You need to have a certain server-side development foundation, and realize the message push function by calling the webhook address of the custom robot by request.

- Custom bots are ready to use after being added to a group, no tenant admin approval required. This feature improves the portability of developing robots, but for the sake of tenant data security, it also limits the usage scenarios of custom robots, and custom robots do not have any data access rights.

- If you want to implement robot group management, user information acquisition and other capabilities, it is recommended to refer to [Session-based interactive robot](https://open.feishu.cn/document/client-docs/bot-v3/(/document/uAjLw4CM/uMzNwEjLzcDMx4yM3ATM/develop-a-card-interactive-bot/introduction)), through the robot application. For a comparison of the capabilities of custom bots and robot applications, see [Comparison of Capabilities](https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/bot-v3/bot-overview#6994dff4).

- The frequency control of the customized robot is different from the normal application, which is 100 times/minute and 5 times/second for single tenant single bot. **It is recommended to avoid sending messages at whole time and half time such as 10:00, 17:30, etc** . Otherwise, there may be 11232 flow limiting error due to system pressure, resulting in failure of message sending.

- When sending a message, the request body data size cannot exceed 20 KB.

## Features

There are scenarios where enterprises automatically push messages to specific groups, for example, pushing monitoring alarms, sales leads, and operational content. In this type of scenario, you can add a custom robot to the group. The custom robot provides a webhook by default. By calling the webhook address from the server, the message notification from the external system can be pushed to the group in real time. The custom robot also includes security configurations in three dimensions: **custom keywords** , **IP whitelist**  and **signature** , which is convenient for controlling the scope of webhook calls.

An example of a custom robot message push, as shown in the following figure:

## Add a custom bot to the group

### Procedure

1. Invite custom robots into the group.

    1.
Enter the target group, click the More button in the upper right corner of the group, and click **Settings** .

    2.
On the **Settings**  interface on the right, click **Bots** .

    3.
On the **Bots**  interface, click **Add Bot** .

    4.
In the **Add bot**  dialog box, find and click **Custom bot** .

    5.
Set the avatar, name and description of the custom robot, and click **Add** .

2. Obtain the webhook address of the custom bot and click **Finish** .

The **Webhook URL**  format corresponding to the robot is as follows:
```
https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxxxxxxxxxxx
```

**Please keep this webhook address properly**  and do not publish it on publicly accessible websites such as Gitlab and blogs to avoid being maliciously called to send spam messages after the address is leaked.

Later, you can click the robot picture to the right of the group name to enter the custom robot details page and manage the configuration information of the custom robot.

1. Test calling the webhook address of the custom robot to send a message to the group it belongs to.

    1.
Initiate an HTTP POST request to the webhook address in any way.

You need to have a certain server-side development foundation, and call the webhook address through the server-side HTTP POST request. Taking the curl command as an example, the request example is as follows. You can execute the following command through the terminal of the macOS system or the console application of the Windows system to test.

        - macOS
```
curl -X POST -H "Content-Type: application/json" \
 -d '{"msg_type":"text","content":{"text":"request example"}}' \
 https://open.feishu.cn/open-apis/bot/v2/hook/****
```

        - Windows(cmd)
```
curl -X POST -H "Content-Type: application/json" -d "{\"msg_type\":\"text\",\"content\":{\"text\":\"request example\"}}" https://open.feishu.cn/open-apis/bot/v2/hook/****
```

        - Windows(PowerShell)
```
curl.exe -X POST -H "Content-Type: application/json" -d '{\"msg_type\":\"text\",\"content\":{\"text\":\"requestexample\"}}' https://open.feishu.cn/open-apis/bot/v2/hook/****
```

Example command description:

        - Request method: `POST`

        - Request header: `Content-Type: application/json`

        - Request body: `{"msg_type":"text","content":{"text":"request example"}}`

        - webhook address: `https://open.feishu.cn/open-apis/bot/v2/hook/****` is an example value, you need to replace it with the real webhook address of your custom robot when actually calling.

When sending a request to a custom robot, it supports sending various message types such as text, rich text, group business card, and message card. For request descriptions of various message types, see [Description of supported message types](https://open.feishu.cn/document/ukTMukTMukTM/ucTM5YjL3ETO24yNxkjN#1b70f1fa).

After executing the command:

        - If the request is successful, the command line will echo the following information.
```
{
         "StatusCode": 0, //Redundant field, for compatibility with stock history logic, not recommended
         "StatusMessage": "success", //Redundant field, for compatibility with stock history logic, not recommended
         "code": 0,
         "data": {},
         "msg": "success"
}
```

        - If the request body format is incorrect, the following information will be returned.
```
{
          "code": 9499,
          "msg": "Bad Request",
          "data": {}
}
```

You can check whether there is a problem with the request body through the following instructions.

        - Whether the content format of the request body is consistent with the sample codes of each message type.

        - The request body size cannot exceed 20K.

    2.
After the command is executed, enter the group where the custom robot is located to view the test message.

### Next Steps

After successfully adding a custom robot, it is recommended that you add security settings for the custom robot to ensure the security of the robot receiving requests. For details, see [Add security settings for custom robots](https://open.feishu.cn/document/ukTMukTMukTM/ucTM5YjL3ETO24yNxkjN#ddf40249).

## Add security settings for custom bots

After adding a custom bot to a group, you can add security settings for the bot. Security settings are used to protect custom robots from being called maliciously. For example, when the webhook address is leaked due to improper storage, it may be called by malicious developers to send spam. By adding security settings, the robot can only be called successfully if the conditions of the security settings are met.

Currently provided security settings are as follows:

- We strongly recommend adding security settings to custom bots for extra security.

- In the same custom bot, you can set one or more methods.

- Custom keywords: Only messages containing at least one keyword can be sent successfully.

- IP whitelist: Only IP addresses in the whitelist can successfully request webhook to send messages.

- Signature Verification: Set the signature. The sent request must pass the signature verification before it can successfully request the webhook to send the message.

### Method 1: Set custom keywords

1. Click the robot icon to the right of the group name to open the robot list, find the custom robot and click to enter the configuration page.

You can also open the bot list in the group settings.

2. In the **Security settings**  area, select **Set Keywords** .

3. Add keywords in the input box.

    - You can set up to 10 keywords at the same time, and use the Enter key to space between multiple keywords. When set, only messages containing at least one keyword will be sent successfully.

For example, if the keywords are set to `Application Alert` and `Project Update`, the message content sent by the request webhook must contain at least one of the keywords `Application Alert` or `Project Update`.

    - After setting keywords, if the custom keyword verification fails when sending a request, the following information will be returned.
```
// Keyword validation failed
{
     "code": 19024,
     "msg": "Key Words Not Found"
}
```

4. Click **Save**  to make the configuration take effect.

**Notice** : Custom keywords are only valid for text parameter values such as `text` and `title`. For example, when sending a rich text message containing a hyperlink tag `{"tag":"a","text":"Please check","href":"http://www.example.com/"}`, the custom keyword will only filter the `text` parameter value, not the `href` parameter value.

### Method 2: Set IP whitelist

1. Click the robot icon to the right of the group name to open the robot list, find the custom robot and click to enter the configuration page.

You can also open the bot list in the group settings.

2. In the **Security settings**  area, select **Set IP whitelist** .

3. Add the IP address in the input box.

    - Support adding IP addresses or address segments, up to 10 can be set, using the Enter key for intervals. Segment input is supported, such as `123.12.1.*` or `123.1.1.1/24`. When set, the robot webhook address will only handle requests from IP whitelisted ranges.

    - After setting the IP whitelist, when the IP address outside the whitelist requests webhook, the verification will fail and the following information will be returned.
```
// IP verification failed
{
     "code": 19022,
     "msg": "Ip Not Allowed"
}
```

4. Click **Save**  to make the configuration take effect.

### Method 3: Set signature verification

1. Click the robot icon to the right of the group name to open the robot list, find the custom robot and click to enter the configuration page.

You can also open the bot list in the group settings.

2. In the **Security settings**  area, select **Set signature verification** .

After selecting the full name verification, the system has provided a secret key by default. You can also click **Reset**  to change the key.

3. Click **Copy**  to copy the key.

4. Click **Save**  to make the configuration take effect.

5. Compute the signature string.

After setting up signature verification, sending a request to the webhook requires signature verification to ensure the source is credible. The verified signature needs to be encrypted by the timestamp and secret key, that is, `timestamp + "\n" + secret key` is used as the signature string, the signature result of the empty string is calculated using the HmacSHA256 algorithm, and then Base64 encoding is performed. Among them, `timestamp` refers to a timestamp that is no more than 1 hour (3600 seconds) from the current time, and the time unit is: s. For example, 1599360473.

This article provides the following code samples in different languages to calculate the signature string.

    - Java sample code
```
package sign;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.nio.charset.StandardCharsets;
import java.security.InvalidKeyException;
import java.security.NoSuchAlgorithmException;
import org.apache.commons.codec.binary.Base64;
public class SignDemo {
  public static void main(String[] args) throws NoSuchAlgorithmException, InvalidKeyException {
    String secret = "demo";
    int timestamp = 1599360473;
 System.out.printf("sign: %s", GenSign(secret, timestamp));
}
  private static String GenSign(String secret, int timestamp) throws NoSuchAlgorithmException, InvalidKeyException {
    //Take timestamp+"\n"+ key as signature string
    String stringToSign = timestamp + "\n" + secret;
    //Use the HmacSHA256 algorithm to calculate the signature
    Mac mac = Mac. getInstance("HmacSHA256");
 mac.init(new SecretKeySpec(stringToSign.getBytes(StandardCharsets.UTF_8), "HmacSHA256"));
    byte[] signData = mac.doFinal(new byte[]{});
    return new String(Base64. encodeBase64(signData));
 }
}
```

    - Go sample code
```
func GenSign(secret string, timestamp int64) (string, error) {
   //timestamp + key do sha256, then base64 encode
 stringToSign := fmt.Sprintf("%v", timestamp) + "\n" + secret
   var data []byte
 h := hmac.New(sha256.New, []byte(stringToSign))
 _, err := h. Write(data)
   if err != nil {
      return "", err
 }
 signature := base64.StdEncoding.EncodeToString(h.Sum(nil))
   return signature, nil
}
```

    - Python sample code
```
import hashlib
import base64
import hmac
def gen_sign(timestamp, secret):
    # Splicing timestamp and secret
 string_to_sign = '{}\n{}'.format(timestamp, secret)
 hmac_code = hmac.new(string_to_sign.encode("utf-8"), digestmod=hashlib.sha256).digest()
    # Perform base64 processing on the result
 sign = base64.b64encode(hmac_code).decode('utf-8')
    return sign
```

6. Get the signature string.

Taking the Java sample code as an example, after obtaining the current timestamp and key, run the program to obtain the signature string.

After obtaining the signature string, when sending a request to the webhook, you need to add the timestamp (timestamp) and signature string (sign) field information. A sample configuration is shown below.
```
// Send a text message after enabling signature verification
{
        "timestamp": "1599360473", // Timestamp.
        "sign": "xxxxxxxxxxxxxxxxxxxxx", // The obtained signature string.
        "msg_type": "text",
        "content": {
                "text": "request example"
        }
}
```

If the verification fails when sending the request, you can troubleshoot the problem through the following instructions.

    - The timestamp used is more than 1 hour from the time the request was sent, and the signature has expired.

    - The server time has a large deviation from the standard time, causing the signature to expire. Please pay attention to check and adjust your server time.

    - If the verification fails due to signature mismatch, the following information will be returned.
```
// signature verification failed
{
        "code": 19021,
        "msg": "sign match fail or timestamp is not within one hour from current time"
}
```

## Delete custom bot

In the **Settings**  of the Feishu group, open the **Bots**  list, find the custom robot that needs to be deleted, and click the delete icon on the right side of the card.

## Description of supported message types

When sending a POST request to a custom robot webhook address, the supported message formats include **text** , **rich text** , **picture message**  and **group business card** , etc. This chapter introduces each message Type request format and display effect.

### Send text message

#### Request message body example

```
{

     "msg_type": "text",

     "content": {

         "text": "new update notification"

     }

}
```
#### Realize the effect

#### Parameter Description

- The value of the parameter `msg_type` is the mapping relationship of the corresponding message type, and the corresponding value of `msg_type` for text messages is `text`.

- The parameter `content` contains the message content, and the description of the message content parameters of the text message is shown in the table below.

| **Field** | **Type** | **Required** | **Example Value** | **Description** |
|---|---|---|---|---|
| text | string | is | Test content | Text content. |

#### @ usage for text messages

```
// @ single user

<at user_id="ou_xxx">Name</at>

// @ all

<at user_id="all">everyone</at>
```
- @ For a single user, the `user_id` field needs to be filled in the user's [Open ID](https://open.feishu.cn/document/uAjLw4CM/ugTN1YjL4UTN24CO1UjN/trouble-shooting/how-to-obtain-openid) or [User ID](https://open.feishu.cn/document/uAjLw4CM/ugTN1YjL4UTN24CO1UjN/trouble-shooting/how-to-obtain-user-id), and must be a valid value (only supports @ group members of the group where the custom robot is located), otherwise the name display will not produce actual @ effect.

