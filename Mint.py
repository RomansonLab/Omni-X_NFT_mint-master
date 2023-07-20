# Импорт необходимых библиотек
import random
import time
import os
from web3 import Web3, HTTPProvider
import json

# Проверка наличия файла конфигурации
if not os.path.isfile('config_user.json'):
    # Запрашиваем у пользователя необходимые детали
    print("You need to set parameter, they can be change any time in 'config_user' file")
    min_mint = input("Enter the minimum number of NFT to mint: ")
    max_mint = input("Enter the maximum number of NFT to mint: ")
    min_delay = input("Enter the minimum delay between actions, in sec: ")
    max_delay = input("Enter the maximum delay between actions, in sec: ")

    # Сохранение ввода пользователя в словаре конфигурации
    config_user = {
        'min_mint': min_mint,
        'max_mint': max_mint,
        'min_delay': min_delay,
        'max_delay': max_delay,
    }

    # Сохранение словаря конфигурации в файл JSON
    with open('config_user.json', 'w') as f:
        json.dump(config_user, f)

    print("Configuration saved successfully.")
else:
    print("Configuration file already exists, it can be change any time in 'config_user' file")

# Загрузка настроек из файла конфигурации
with open('config_user.json', 'r') as f:
    config_user = json.load(f)

# Доступ к настройкам в скрипте
min_mint = float(config_user['min_mint'])
max_mint = float(config_user['max_mint'])
min_delay = float(config_user['min_delay'])
max_delay = float(config_user['max_delay'])

# Загрузка ABI контракта (Application Binary Interface) из файла JSON
# ABI позволяет Python взаимодействовать с функциями контракта
with open("Contraht_ABI.JSON", 'r') as f:
    config = json.load(f)

# Чтение приватных ключей из текстового файла.
# Каждый приватный ключ должен быть на новой строке в текстовом файле
with open('private_keys.txt', 'r') as f:
    private_keys = [line.strip() for line in f]

# Определение функции OmniNFT, которая взаимодействует с контрактом NFT
def OmniNFT(private_key):
    # Установка соединения с сетью Ethereum
    w3 = Web3(HTTPProvider("https://rpc.ankr.com/optimism"))

    # Генерация объекта аккаунта из предоставленного приватного ключа
    account = w3.eth.account.from_key(private_key)

    # Указание имени контракта для взаимодействия
    contract_name = "OMNIA"

    # Извлечение деталей контракта из загруженной конфигурации
    contract_details = config['contracts'][contract_name]

    # Получение адреса контракта и преобразование его в корректный формат
    contract_address = w3.to_checksum_address(contract_details['address'])
    contract = w3.eth.contract(address=contract_address, abi=contract_details['ABI'])

    # Выбор случайного количества токенов для выпуска
    _nbTokens = int(round(random.uniform(min_mint, max_mint)))

    # Оценка необходимого газа для выпуска токенов
    estimated_gas = contract.functions.mint(_nbTokens).estimate_gas({'from': account.address, })

    # Расчет лимита газа и цены газа для транзакции
    gas_limit = int(estimated_gas * 1.5)
    max_gwei = round(random.uniform(0.001397986, 0.002397986 ), 9)
    max_priority_gwei = round(random.uniform(0.000000350, 0.000000600), 9)
    max_wei = max_gwei * 1e9
    max_priority_wei = max_priority_gwei * 1e9

    # Создание транзакции, которая будет выпускать токены
    transaction = contract.functions.mint(_nbTokens).build_transaction({
        'nonce': w3.eth.get_transaction_count(account.address),
        'gas': gas_limit,
        'maxFeePerGas': int(max_wei),
        'maxPriorityFeePerGas': int(max_priority_wei),
    })

    # Подписание транзакции с помощью приватного ключа
    signed_txn = w3.eth.account.sign_transaction(transaction, private_key)

    # Отправка подписанной транзакции в сеть Optimism
    txn_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)

    # Ожидание майнинга транзакции и получение квитанции о транзакции
    txn_receipt = w3.eth.wait_for_transaction_receipt(txn_hash, timeout=666)

    # Проверка успешности транзакции
    if txn_receipt['status'] == 1:
        print(f">>> {contract_name} mint was successful")
        print(f"Transaction Hash: {txn_hash.hex()}")
        print(f" ")
        with open('success.txt', 'a') as success_file:
            success_file.write(f"{account.address} | {txn_hash.hex()}\n")
        return 1, txn_hash.hex()
    else:
        print("Transaction was unsuccessful.")
        print(f"Transaction Hash: {txn_hash.hex()}")
        with open('failure.txt', 'a') as failure_file:
            failure_file.write(f"{account.address} | {txn_hash.hex()}\n")
        return 0, txn_hash.hex()

def remove_key_from_file(key):
    """Удаляет одну строку из файла, содержащую данный ключ."""
    with open('private_keys.txt', 'r') as f:
        lines = f.readlines()
    with open('private_keys.txt', 'w') as f:
        removed = False
        for line in lines:
            if line.strip("\n") == key and not removed:
                removed = True
            else:
                f.write(line)
        # If the key was not found in the file, write a warning
        if not removed:
            print(f"Warning: Key '{key}' not found in the file.")

# Перемешивание списка приватных ключей
random.shuffle(private_keys)

# Вызов функции OmniNFT для каждого приватного ключа в перемешанном списке
for key in private_keys:
    status, transaction_hash = OmniNFT(key)
    if status == 1:  # Если выпуск токенов был успешным, удалить приватный ключ из файла
        remove_key_from_file(key)
    plaseholder = round(random.uniform(min_delay, max_delay))
    current_time = time.strftime('%Y-%m-%d %H:%M:%S')  # Get the current timestamp
    print(f"{current_time} - Wait {plaseholder} second before next operation...")
    time.sleep(plaseholder)

