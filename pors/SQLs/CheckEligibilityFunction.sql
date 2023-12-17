CREATE FUNCTION dbo.CheckEligibilityFunction
    (
        @inputDate DATE,
        @mealType VARCHAR(3)
    )
RETURNS BIT
AS
BEGIN
    DECLARE @now DATETIME = GETDATE();
    DECLARE @deadline INT;
    DECLARE @eligibleDate DATETIME;
    DECLARE @res BIT

    -- Determine the deadline based on meal type
    SELECT @deadline =
        CASE
            WHEN @mealType = 'LNC' THEN m.LaunchRegistrationWindowHours
            WHEN @mealType = 'BRF' THEN m.BreakfastRegistrationWindowHours
        END
    FROM dbo.pors_systemsetting m;

    -- Add the deadline to the current date
    SET @eligibleDate = DATEADD(HOUR, @deadline, @now);

    -- Compare the input date with the eligible date
    IF @eligibleDate < @inputDate
    BEGIN
        SET @res= 1;
    END
    ELSE
    BEGIN
        SET @res= 0;
    END
RETURN @res
END
go

