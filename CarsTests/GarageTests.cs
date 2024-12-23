using Microsoft.VisualStudio.TestTools.UnitTesting;
using System;
using System.IO;
using System.Runtime.ConstrainedExecution;
using ProgForTest;
using System.Collections.Generic;
using System.IO;

namespace CarsTests
{
    [TestClass]
    public class GarageTests
    {
        private Garage _garage;

        [TestInitialize]
        public void Setup()
        {
            _garage = new Garage();
        }

        [TestMethod]
        public void AddCar_ToGarage() // Проверяет, что добавленный автомобиль действительно находится в гараже.
        {
            var car = new Car("Toyota", "Camry", 2020, 15000);

            // Добавляем автомобиль в гараж.
            _garage.AddCar(car);

            // Проверяем, что автомобиль был добавлен.
            var cars = _garage.SearchCar("Toyota");
            Assert.AreEqual(1, cars.Count); // Ожидаем, что в гараже будет 1 автомобиль.
            Assert.AreEqual(car, cars[0]); // Ожидаем, что это именно тот автомобиль, который мы добавили.
        }

        [TestMethod]
        public void RemoveCar_FromGarage() // Проверяет, что удаленный автомобиль больше не находится в гараже.
        {
            var car = new Car("Honda", "Civic", 2019, 20000);
            var car2 = new Car("Ford", "Mustang", 2021, 5000);
            _garage.AddCar(car);
            _garage.AddCar(car2);

            // Удаляем автомобиль из гаража.
            _garage.RemoveCar(car);

            // Проверяем, что автомобиль был удален.
            var cars = _garage.SearchCar("Honda");
            Assert.AreEqual(0, cars.Count); // Ожидаем, что в гараже не останется автомобилей Honda.
        }

        [TestMethod]
        public void SearchCar_CorrectCars() // Проверяет, что поиск по производителю возвращает правильный автомобиль.
        {
            var car1 = new Car("Ford", "Mustang", 2021, 5000);
            var car2 = new Car("Honda", "Civic", 2019, 20000);
            _garage.AddCar(car1);
            _garage.AddCar(car2);

            // Поиск автомобиля 
            var searchResults = _garage.SearchCar("Ford");

            // Проверяем, что найденный автомобиль соответствует ожиданиям.
            Assert.AreEqual(1, searchResults.Count); // Ожидаем, что будет найден 1 автомобиль.
            Assert.AreEqual(car1, searchResults[0]); // Ожидаем, что это будет Ford Mustang.
        }

        [TestMethod]
        public void SearchCar_MatchingName() // Проверяет, что поиск по названию возвращает правильные автомобили.
        {
            var car1 = new Car("Toyota", "Camry", 2020, 15000);
            var car2 = new Car("Honda", "Civic", 2019, 20000);
            var car3 = new Car("Ford", "Mustang", 2021, 5000);
            _garage.AddCar(car1);
            _garage.AddCar(car2);
            _garage.AddCar(car3);

            // Выполняем поиск по названию.
            var searchResults = _garage.SearchCar("Cam");

            // Проверяем, что найденный автомобиль соответствует ожиданиям.
            Assert.AreEqual(1, searchResults.Count); // Ожидаем, что будет найден только один автомобиль.
            Assert.AreEqual(car1, searchResults[0]); // Ожидаем, что это будет Toyota Camry.
        }

        [TestMethod]
        public void DisplayCars_CorrectMessage() // Проверяет, что при вызове метода DisplayCars в пустом гараже выводится правильное сообщение.
        {
            // Вызываем метод DisplayCars и захватываем вывод.
            var output = CaptureConsoleOutput(() => _garage.DisplayCars());

            // Проверяем, что вывод соответствует ожиданиям.
            Assert.AreEqual("\nГараж пуст.\r\n", output); // Ожидаем сообщение о том, что гараж пуст.
        }

        [TestMethod]
        public void DisplayCars_AllCars() // Проверяет, что при наличии автомобилей в гараже выводятся все автомобили с правильной информацией.
        {
            var car1 = new Car("Mercedes Benz", "Maybach", 2022, 9000);
            var car2 = new Car("Honda", "Jazz", 2023, 1000);
            _garage.AddCar(car1);
            _garage.AddCar(car2);

            // Вызываем метод DisplayCars и захватываем вывод.
            var output = CaptureConsoleOutput(() => _garage.DisplayCars());

            // Проверяем, что вывод содержит информацию о всех автомобилях в гараже.
            Assert.IsTrue(output.Contains("2022 Mercedes Benz Maybach - Пробег: 9000 км")); // Проверяем, что информация о первом автомобиле присутствует в выводе.
            Assert.IsTrue(output.Contains("2023 Honda Jazz - Пробег: 1000 км")); // Проверяем, что информация о втором автомобиле присутствует в выводе.
        }

        // Метод для захвата вывода в консоль.
        private string CaptureConsoleOutput(Action action)
        {
            var originalOut = Console.Out;
            using (var sw = new StringWriter()) 
            {
                Console.SetOut(sw); 
                action(); 
                Console.SetOut(originalOut);
                return sw.ToString(); 
            }
        }
    }
}
