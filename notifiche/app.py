import pika, sys, os

def main():
    rabbitmq_host = os.environ.get('RABBITMQ_HOST', 'rabbitmq')
    rabbitmq_port = int(os.environ.get('RABBITMQ_PORT', 5672))
    rabbitmq_user = os.environ.get('RABBITMQ_USER', 'user')
    rabbitmq_password = os.environ.get('RABBITMQ_PASSWORD', 'password')

    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host, port=rabbitmq_port, credentials=pika.PlainCredentials(rabbitmq_user, rabbitmq_password),heartbeat=600))
    channel = connection.channel()
   

    channel.queue_declare(queue='notifications')

    def callback(ch, method, properties, body):
        print(f" [x] Received {body}")

    channel.basic_consume(queue='notifications',
                        auto_ack=True,
                        on_message_callback=callback)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
