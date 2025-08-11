from tabulate import tabulate
from loguru import logger
import pandas as pd
from datetime import datetime
import os

from src.utils.config import Config, WalletInfo


def print_wallets_stats(config: Config, excel_path="data/progress.xlsx"):
    """
    Выводит статистику по всем кошелькам в виде таблицы и сохраняет в Excel файл

    Args:
        config: Конфигурация с данными кошельков
        excel_path: Путь для сохранения Excel файла (по умолчанию "data/progress.xlsx")
    """
    try:
        # Сортируем кошельки по индексу
        sorted_wallets = sorted(config.WALLETS.wallets, key=lambda x: x.account_index)

        # Подготавливаем данные для таблицы
        table_data = []
        total_balance = 0
        total_transactions = 0
        total_points = 0
        total_quests = 0
        ranks = []
        wallets_with_somnia_data = 0

        for wallet in sorted_wallets:
            # Маскируем приватный ключ (последние 5 символов)
            masked_key = "•" * 3 + wallet.private_key[-5:]

            total_balance += wallet.balance
            total_transactions += wallet.transactions

            # Обрабатываем Somnia данные для статистики
            if wallet.final_points and wallet.final_points != "N/A":
                try:
                    points = float(wallet.final_points)
                    total_points += points
                    wallets_with_somnia_data += 1
                except (ValueError, TypeError):
                    pass
            
            if wallet.quests_completed and wallet.quests_completed != "N/A":
                try:
                    quests = int(wallet.quests_completed)
                    total_quests += quests
                except (ValueError, TypeError):
                    pass
            
            if wallet.rank and wallet.rank not in ["N/A", "Not ranked"]:
                try:
                    rank = int(wallet.rank)
                    ranks.append(rank)
                except (ValueError, TypeError):
                    pass

            row = [
                str(wallet.account_index),  # Просто номер без ведущего нуля
                wallet.address,  # Полный адрес
                masked_key,
                f"{wallet.balance:.4f} ETH",
                f"{wallet.transactions:,}",  # Форматируем число с разделителями
                wallet.final_points if wallet.final_points else "N/A",
                wallet.rank if wallet.rank else "N/A",
                wallet.quests_completed if wallet.quests_completed else "N/A",
            ]
            table_data.append(row)

        # Если есть данные - выводим таблицу и статистику
        if table_data:
            # Создаем заголовки для таблицы
            headers = [
                "№ Account",
                "Wallet Address",
                "Private Key",
                "Balance (ETH)",
                "Total Txs",
                "Final Points",
                "Rank",
                "Quests Done",
            ]

            # Формируем таблицу с улучшенным форматированием
            table = tabulate(
                table_data,
                headers=headers,
                tablefmt="double_grid",  # Более красивые границы
                stralign="center",  # Центрирование строк
                numalign="center",  # Центрирование чисел
            )

            # Считаем средние значения
            wallets_count = len(sorted_wallets)
            avg_balance = total_balance / wallets_count
            avg_transactions = total_transactions / wallets_count

            # Выводим таблицу и статистику
            logger.info(
                f"\n{'='*50}\n"
                f"         Wallets Statistics ({wallets_count} wallets)\n"
                f"{'='*50}\n"
                f"{table}\n"
                f"{'='*50}\n"
                f"{'='*50}"
            )

            logger.info(f"Average balance: {avg_balance:.4f} ETH")
            logger.info(f"Average transactions: {avg_transactions:.1f}")
            logger.info(f"Total balance: {total_balance:.4f} ETH")
            logger.info(f"Total transactions: {total_transactions:,}")

            # Somnia статистика
            if wallets_with_somnia_data > 0:
                logger.info(f"Total points: {total_points:.1f}")
                avg_quests = total_quests / wallets_with_somnia_data if wallets_with_somnia_data > 0 else 0
                logger.info(f"Average quests done: {avg_quests:.1f}")
                
                if ranks:
                    min_rank = min(ranks)
                    max_rank = max(ranks)
                    logger.info(f"Best rank: {min_rank:,} (lower is better)")
                    logger.info(f"Worst rank: {max_rank:,}")

            # Экспорт в Excel
            # Создаем DataFrame для Excel
            df = pd.DataFrame(table_data, columns=headers)

            # Добавляем итоговую статистику
            summary_data = [
                ["", "", "", "", "", "", "", ""],
                ["SUMMARY", "", "", "", "", "", "", ""],
                [
                    "Total",
                    f"{wallets_count} wallets",
                    "",
                    f"{total_balance:.4f} ETH",
                    f"{total_transactions:,}",
                    f"{total_points:.1f}" if wallets_with_somnia_data > 0 else "N/A",
                    f"Best: {min(ranks):,}" if ranks else "N/A",
                    f"{total_quests}" if wallets_with_somnia_data > 0 else "N/A",
                ],
                [
                    "Average",
                    "",
                    "",
                    f"{avg_balance:.4f} ETH",
                    f"{avg_transactions:.1f}",
                    f"{total_points/wallets_with_somnia_data:.1f}" if wallets_with_somnia_data > 0 else "N/A",
                    f"Worst: {max(ranks):,}" if ranks else "N/A", 
                    f"{total_quests/wallets_with_somnia_data:.1f}" if wallets_with_somnia_data > 0 else "N/A",
                ],
            ]
            summary_df = pd.DataFrame(summary_data, columns=headers)
            df = pd.concat([df, summary_df], ignore_index=True)

            # Создаем директорию, если она не существует
            os.makedirs(os.path.dirname(excel_path), exist_ok=True)

            # Формируем имя файла с датой и временем
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"progress_{timestamp}.xlsx"
            file_path = os.path.join(os.path.dirname(excel_path), filename)

            # Сохраняем в Excel
            df.to_excel(file_path, index=False)
            logger.info(f"Statistics exported to {file_path}")
        else:
            logger.info("\nNo wallet statistics available")

    except Exception as e:
        logger.error(f"Error while printing statistics: {e}")
