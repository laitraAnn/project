using System;

namespace ProgForTest
{
    public class Car
    {
        public string Make { get; set; }
        public string Model { get; set; }
        public int Year { get; set; }
        public decimal Mileage { get; set; }

        public Car(string make, string model, int year, decimal mileage)
        {
            Make = make;
            Model = model;
            Year = year;
            Mileage = mileage;
        }

        public override string ToString()
        {
            return $"{Year} {Make} {Model} - Пробег: {Mileage} км";
        }
    }
}