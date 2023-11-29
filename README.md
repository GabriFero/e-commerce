# Progetto E-commerce

Questo progetto è diviso in 4 microservizi:

1. **Libri**: gestisce le informazioni sui libri disponibili per il prestito, come il titolo, l’autore, il genere, il prezzo, ecc.
2. **Notifiche**: invia notifiche quando ad esempio viene aggiunto un nuovo libro oppure viene eliminato un utente.
3. **Prestiti**: gestisce le operazioni di prestito dei libri, come la registrazione,la restituzione.
4. **Utenti**: gestisce le informazioni sugli utenti, come il nome, l’email, il numero di telefono, ecc.

## Requisiti

Per eseguire il progetto, è necessario avere installato Python 3 o superiore e Docker. Inoltre, è necessario installare le dipendenze elencate nel file requirements.txt usando il comando:

pip install -r requirements.txt

## Tecnologie utilizzate
Python3.6
Docker
Flask
Postgresql
MariaDB
RabbitMQ

## Esecuzione

Per avviare il progetto, è sufficiente eseguire il file docker-compose.yml usando il comando:

docker-compose up --b

Questo creerà e avvierà i container Docker per i quattro moduli e il database. 

## Test

Per eseguire i test, è possibile usare il comando: pytest --cov=app . all'interno del rispettivo container docker

es: entrare nella cartella app/libri ed eseguire il seguente comando pytest --cov=app .

## Logging

Per monitorare le attività e gli errori del progetto, è possibile usare il modulo logging. Il progetto registra i messaggi di log in un file chiamato app.log nella cartella principale del container.

per controllare i log eseguire il seguente comando cat app.log

## Notifiche

Per controllare le notifiche inviate da rabbitMQ entrare nella cartella principale del container notifiche ed eseguire il seguente comando:

python notifiche.py 

a questo punto ogni evento che accadrà all'interno dei microservizi, verrà registrato in questo terminale.



