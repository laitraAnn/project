using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.ConstrainedExecution;
using System.Text;
using System.Threading.Tasks;

namespace ProgForTest
{
    internal class Program
    {
        static void Main(string[] args)
        {
            string make = "", model = "";
            int year;
            decimal mileage;
            string command;
            Garage garage = new Garage();

            Car car1 = new Car("Toyota", "Camry", 2020, 15000);
            Car car2 = new Car("Honda", "Civic", 2019, 20000);
            Car car3 = new Car("Ford", "Mustang", 2021, 5000);
            Car car4 = new Car("Honda", "Mustуауang", 2021, 5000);

            garage.AddCar(car1);
            garage.AddCar(car2);
            garage.AddCar(car3);
            garage.AddCar(car4);

            Console.Clear();
            do
            {
                Console.WriteLine("Выберите действие:");
                Console.WriteLine("1. Добавить автомобиль");
                Console.WriteLine("2. Удалить автомобиль");
                Console.WriteLine("3. Найти автомобиль");
                Console.WriteLine("4. Показать все автомобили");
                Console.WriteLine("0. Выход");
                Console.Write("Ваше действие (введите цифру): ");
                command = Console.ReadLine();

                switch (command)
                {
                    case "1":
                        Console.Write("Введите производителя: ");
                        make = Console.ReadLine();
                        Console.Write("Введите модель: ");
                        model = Console.ReadLine();
                        Console.Write("Введите год выпуска: ");
                        while (!int.TryParse(Console.ReadLine(), out year)){
                            Console.WriteLine("Неверная команда. Пожалуйста, попробуйте снова.");
                            Console.Write("Введите год выпуска: ");
                        }
                        Console.Write("Введите пробег: ");
                        
                        
                        while (!decimal.TryParse(Console.ReadLine(),out mileage))
                        {
                            Console.WriteLine("Неверная команда. Пожалуйста, попробуйте снова.");
                            Console.Write("Введите пробег: ");
                        }
                        
                        Car newCar = new Car(make, model, year, mileage);
                        garage.AddCar(newCar);
                        break;
                    case "2":
                        
                        Console.Write("Введите производителя автомобиля для удаления: ");
                        make = Console.ReadLine();
                        Console.Write("Введите модель автомобиля для удаления: ");
                        model = Console.ReadLine();

                        var carToRemove = garage.SearchCar(make).FirstOrDefault(c => c.Model.Equals(model, StringComparison.OrdinalIgnoreCase));

                        if (carToRemove != null)
                        {
                            garage.RemoveCar(carToRemove);
                        }
                        else
                        {
                            Console.WriteLine("Автомобиль не найден.");
                        }
                        break;
                    case "3":
                        Console.Write("\nКакую машину вы ищите (введите модель или производителя): ");
                        var searchResults = garage.SearchCar(Console.ReadLine());
                        foreach (var car in searchResults)
                        {
                            Console.WriteLine(car);
                        }
                        break;
                    case "4":
                        garage.DisplayCars();
                        break;
                    case "0":
                        Console.WriteLine("Выход из программы.");
                        break;
                    default:
                        Console.WriteLine("Неверная команда. Пожалуйста, попробуйте снова.");
                        break;
                }
                Console.ReadKey();
                Console.Clear();
            } while (command != "0");
        }
    }
    }
