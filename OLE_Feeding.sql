{\rtf1\ansi\ansicpg1252\cocoartf2820
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fnil\fcharset0 Menlo-Regular;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww29200\viewh15660\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 \'97- This is the stored procedure for sending the trades/deals from Little Dragon to OLE. OLE is the Back office for Security trades/deals. Note that Trades and Deals mean the same.\
CREATE PROCEDURE goat\
    @date datetime = NULL,\
    @deal int = NULL\
AS\
BEGIN\
    DECLARE @error int,\
            @error_message nvarchar(4000),\
            @date_begin datetime,\
            @date_end datetime;\
\
    BEGIN TRY\
        -- Temporary table creation\
        CREATE TABLE #ABC_tmp (\
            deal int, -- Trade or Deal ID\
            ldate datetime, -- Last modified date of the trade\
            qty int,  --  Quantity of the deal\
            portfolio char(10),\
            status char(10), \'97- Status of the trade. I or R.\
            market char(10),\'97- Market to which the trade belongs to\
            unit_price float, \'97- Unit price of the trade\
            type char(10), -- Type of the trade. It can SECURITY or FUTURE.\
            tax_amount float DEFAULT 0,\
            total_price float,\
            date_stop datetime\
        );\
\
        -- Insert data into temporary table to get all the eligible trades for feeding.\
        INSERT INTO #ABC_tmp (deal, ldate, qty, portfolio, status, market, unit_price, type, total_price, date_stop)\
        SELECT \
            a.deal,\
            a.ldate,\
            a.qty,\
            a.portfolio,\
            a.status, \
            a.market,\
            a.unit_price,\
            a.type,\
            a.qty * a.unit_price,\
            a.date_stop\
        FROM ABC a\
        INNER JOIN port p \
            ON a.portfolio = p.portfolio\
        WHERE \
            a.deal = @deal \'97- This takes the deal id from the prompt.\
            AND a.ldate = @date \'97- Taking the last modified date of the trade.\
            AND a.status IN ('I', 'R') -- Status should only be I or R\
            AND a.date_stop IS NULL \
            AND a.type = 'SECURITY' --Selecting only SECURITY trades for the feeding. This is because only Security trades are sent to OLE. Other types (like Futures, Options etc) are not sent to OLE application.\
            ;\
\
        -- Check for unit_price exceeding 10 digits\
        IF EXISTS (\
            SELECT 1 \
            FROM #ABC_tmp \
            WHERE LEN(CAST(unit_price AS bigint)) > 10\
            )\
        BEGIN\
            THROW 50001, 'Price length validation failed: unit_price exceeds 10 digits for Deal ID: ' + CAST(deal AS varchar(20)), 1; \'97- Only the prices upto 1 Billion is allowed to send to OLE. \
        END\
        \
        -- Update tax_amount and adjust total_price\
        UPDATE o\
        SET \
            o.tax_amount = n.tax_amount,\
            o.total_price = o.total_price + n.tax_amount\
        FROM #ABC_tmp o\
        INNER JOIN TAX n\
            ON o.deal = n.deal AND o.ldate = n.ldate\
        WHERE n.tax_amount IS NOT NULL;\
\
        -- Recalculate total_price for specific market. Some markets have their own calcuation for the Total price. In this block it's calcuated.\
        UPDATE o\
        SET \
            o.total_price = o.qty * o.unit_price -- Re calculating the Total Price for the given market.\
        FROM #ABC_tmp o\
        WHERE o.market = 'NSE'; -- If the Market is NSE, then the tax amount is not calcuated for the Total price. \
\
        -- Select the result set\
        SELECT\
            deal,\
            ldate,\
            qty,\
            portfolio,\
            unit_price,\
            type,\
            market,\
            tax_amount,\
            total_price\
        FROM #ABC_tmp;\
\
    END TRY\
    BEGIN CATCH\
        SET @error = ERROR_NUMBER();\
        SET @error_message = ERROR_MESSAGE();\
        RAISERROR('An error occurred in procedure GOAT. Error %d: %s', 16, 1, @error, @error_message);\
        RETURN @error;\
    END CATCH\
END;\
}