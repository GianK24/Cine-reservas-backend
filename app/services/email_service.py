def send_email(ses_client, to_address, subject, body):
    try:
        response = ses_client.send_email(
            Source="reservascine@gmail.com", 
            Destination={
                'ToAddresses': [to_address]
            },
            Message={
                'Subject': {
                    'Data': subject
                },
                'Body': {
                    'Text': {
                        'Data': body
                    }
                }
            }
        )
        return response
    except Exception as e:
        print("Error enviando correo:", e)
        return None
