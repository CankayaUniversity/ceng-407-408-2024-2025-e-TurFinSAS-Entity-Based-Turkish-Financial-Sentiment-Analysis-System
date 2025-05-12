# ceng-407-408-2024-2025-e-TurFinSAS-Entity-Based-Turkish-Financial-Sentiment-Analysis-System
e-TurFinSAS: Entity Based Turkish Financial Sentiment Analysis System

# Project Description
This project aims to collect tweets shared on Twitter X about the top 100 companies listed on Borsa Istanbul (BIST100) and perform entity-based sentiment analysis on this data. Tweets will be classified as positive, negative, or neutral to analyze companies' social media perception and market dynamics. This approach will assist investors and analysts in predicting trends and help companies with brand strategies. Additionally, it will strengthen decision support mechanisms by developing early warning systems against financial crises.

## Team Members

| Name                                 | Student Number  |
|--------------------------------------|-----------------|
| [Taner Onur UYAR](https://github.com/OnurUyar)            | 202011014       |
| [Ahmet Eren YAĞLI](https://github.com/Afumett0)                  | 202011038       |
| [Ahmet Gökay ÜRKMEZ](https://github.com/Gokay6051)              | 202011057       |
| [Mert Şerafettin KARGI](https://github.com/mertserafett1n)                       | 202011061       |
| [Baha ÖÇALAN](https://github.com/bahcln)            | 202011056       |


# Advisor
Dr. Gül TOKDEMİR

## NER Model Files
Click the link for the Turkish Named Entity Recognation (NER) model customized for BIST: https://drive.google.com/drive/folders/1UXAy07fcopcVe7cwXuWTWOtEmTpKpagW?usp=drive_link

# User Manual
## e-TurFinSAS App
eTurFinsas is flask based application that allows users to see and track BIST100 stocks. Users can track informations about the stocks, compare them and see analysis about them.

## App Features:
### User Authentication: Different app experience user to user
### Stock Details: Users can see various stock details.
### Real time data: App and models works with real time market data.

## e-TurFinSAS User Guide
## Login/Sign Up
The Login/Register page allows users to sign in if they already have an account. If they don't have an account, users can register to the app by clicking to the register button. Users can complete their registiretions by entering an email, password and image.

## Admin Page
An admin can login to the app from the Login/Register page using his admin password. This login type unlocks some additional features that allows the admin to control the app. On admin panel, admin can see all the users and their informations. Admin can change the user information, hence he can delete an user.

## Main Page
The Main page shows the main functionalities of the app and help the users to navigate in the app. In the main page, users can see stocks and their relative informations, compare the stocks with each other, see a detailed analyis and add any stock to favorites to follow them easly.

## Stock Table Page
In this page, users can select how much stock they can see at once or search the desired stock. Then, the app shows the user stock, its symbol, current price, the amount of price change and its ratio, the time and a button to add the stock to favorites.

## Compare Stocks Page
The page's main purpose is to show comparison of the selected stocks. This comparison feature helps usersto understand the differences between stocks.

## Detailed Analysis Page
This page shows users the market statistics, performance history, real time stock details and news/analysis about the stock. Detailed analysis page allows users to view variety of details about stock market shares for companies listed on BIST100.  

## Favorites
The favorites feature allows users to add stocks they want to follow to their favorites, allowing them to easily access and follow them.

