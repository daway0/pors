CREATE FUNCTION [dbo].[PersianToMiladi]
(
    @PersianDate VARCHAR(10)
)
RETURNS DATE
AS
BEGIN
    SET @PersianDate = RIGHT (@PersianDate, 9)
    DECLARE @Year INT = SUBSTRING(@PersianDate, 1, 3)
    DECLARE @Month INT = SUBSTRING(@PersianDate, 5, 2)
    DECLARE @Day INT = SUBSTRING(@PersianDate, 8, 2)
    DECLARE @DiffYear INT = @Year - 350

    DECLARE @Days INT = @DiffYear * 365.24 +
    CASE WHEN @Month < 7 THEN (@Month - 1) * 31
         ELSE 186 + (@Month - 7) * 30 END + @Day

    DECLARE @StartDate DATETIME = '03/21/1971'
    DECLARE @ResultDate DATE = @StartDate + @Days

    RETURN CONVERT(DATE, @ResultDate)

END
go
