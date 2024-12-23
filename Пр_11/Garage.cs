using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.ConstrainedExecution;

namespace ProgForTest
{
    public class Garage
    {
        private List<Car> cars;

        public Garage()
        {
            cars = new List<Car>();
        }

        public void AddCar(Car car)
        {
            cars.Add(car);
            Console.WriteLine($"\nМашина добавлена: {car}");
        }

        public void RemoveCar(Car car)
        {
            if (cars.Remove(car))
            {
                Console.WriteLine($"\nУдалена машина: {car}");
            }
            else
            {
                Console.WriteLine("\nМашина не найдена.");
            }
        }

        public List<Car> SearchCar(string searchTerm)
        {
            return cars.Where(c => c.Make.Contains(searchTerm) ||
                                        c.Model.Contains(searchTerm)).ToList();
        }

        
        public void DisplayCars()
        {
            if (cars.Count == 0)
            {
                Console.WriteLine("\nГараж пуст.");
            }
            else
            {
                Console.WriteLine("\nМашин в гараже:");
                foreach (var car in cars)
                {
                    Console.WriteLine(car);
                }
            }
        }
    }
}